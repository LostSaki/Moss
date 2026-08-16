from __future__ import annotations

import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from moss.components import ensure_components, run_verb
from moss.diagnose import RecipeMatch, load_recipes, match_log
from moss.paths import logs_dir
from moss.prefix import apply_windows_version, create_prefix, wine_env
from moss.runtime import Runtime, detect_runtime
from moss.store import Game, upsert
from moss.wrappers import wrap_command

MAX_RETRIES = 3

ANTICHEAT_RECIPES = frozenset({"eac_unsupported", "battleye_unsupported"})

# Active long-running process (for Stop)
_active: dict[str, Any] = {"proc": None, "game_id": "", "started": 0.0}


def _parse_args(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def _command(runtime: Runtime, exe: Path, extra_args: list[str]) -> list[str]:
    if runtime.kind == "proton":
        return [str(runtime.binary), "run", str(exe), *extra_args]
    return [str(runtime.binary), str(exe), *extra_args]


def _workdir(game: Game) -> Path:
    if game.working_dir:
        p = Path(game.working_dir)
        if p.is_dir():
            return p
    return Path(game.exe).parent


def _dll_overrides_env(game: Game) -> str:
    parts: list[str] = []
    for dll, mode in (game.dll_overrides or {}).items():
        name = str(dll).strip()
        if not name:
            continue
        parts.append(f"{name}={str(mode).strip() or 'n,b'}")
    overrides_lower = {k.lower() for k in (game.dll_overrides or {})}
    if game.dxvk_enabled:
        for dll in ("d3d11", "d3d10", "d3d10core", "d3d10_1", "dxgi"):
            if dll not in overrides_lower:
                parts.append(f"{dll}=n,b")
    if game.vkd3d_enabled:
        if "d3d12" not in overrides_lower:
            parts.append("d3d12=n,b")
    else:
        if "d3d12" not in overrides_lower:
            parts.append("d3d12=b")
    return ";".join(parts)


def apply_profile(game: Game) -> Game:
    """Return a shallow-adjusted view of game with active launch profile applied."""
    profiles = list(getattr(game, "launch_profiles", None) or [])
    active = str(getattr(game, "active_profile_id", "") or "")
    if not active or not profiles:
        return game
    match = next((p for p in profiles if str(p.get("id")) == active), None)
    if not match:
        return game
    # Mutate a copy via dataclass replace pattern
    from dataclasses import replace

    kwargs: dict[str, Any] = {}
    if match.get("launch_args") is not None:
        kwargs["launch_args"] = str(match.get("launch_args") or "")
    if match.get("runner_id") is not None:
        kwargs["runner_id"] = str(match.get("runner_id") or "")
    if isinstance(match.get("env_vars"), dict):
        merged = dict(game.env_vars or {})
        merged.update({str(k): str(v) for k, v in match["env_vars"].items()})
        kwargs["env_vars"] = merged
    return replace(game, **kwargs) if kwargs else game


def build_launch_env(game: Game, runtime: Runtime) -> dict[str, str]:
    env = wine_env(runtime, Path(game.prefix))
    env["WINEDEBUG"] = "+err,+fixme"
    if not game.dxvk_enabled and runtime.kind == "proton":
        env["PROTON_USE_WINED3D"] = "1"
    elif game.dxvk_enabled and runtime.kind == "proton":
        env["PROTON_USE_WINED3D"] = "0"
    if getattr(game, "esync_enabled", True):
        env.setdefault("WINEESYNC", "1")
    else:
        env["WINEESYNC"] = "0"
    if getattr(game, "fsync_enabled", True):
        env.setdefault("WINEFSYNC", "1")
    else:
        env["WINEFSYNC"] = "0"
    overrides = _dll_overrides_env(game)
    if overrides:
        existing = env.get("WINEDLLOVERRIDES", "")
        env["WINEDLLOVERRIDES"] = f"{existing};{overrides}".strip(";") if existing else overrides
    if game.windows_version:
        env["MOSS_WINDOWS_VERSION"] = game.windows_version
    for key, value in (game.env_vars or {}).items():
        if key:
            env[str(key)] = str(value)
    return env


def build_launch_command(game: Game, runtime: Runtime) -> tuple[list[str], dict[str, str], list[str]]:
    env = build_launch_env(game, runtime)
    args = _parse_args(game.launch_args)
    base = _command(runtime, Path(game.exe), args)
    return wrap_command(game, base, env)


def active_launch() -> dict[str, Any]:
    proc: subprocess.Popen | None = _active.get("proc")
    running = bool(proc is not None and proc.poll() is None)
    started = float(_active.get("started") or 0)
    return {
        "running": running,
        "gameId": _active.get("game_id") or "",
        "pid": (proc.pid if proc and running else None),
        "startedAt": datetime.fromtimestamp(started, tz=timezone.utc).isoformat(timespec="seconds")
        if started
        else "",
        "durationSec": int(time.time() - started) if running and started else 0,
    }


def stop_active_launch(force: bool = False) -> dict[str, Any]:
    proc: subprocess.Popen | None = _active.get("proc")
    if proc is None or proc.poll() is not None:
        _active["proc"] = None
        return {"ok": False, "message": "No running game process."}
    try:
        if force:
            proc.kill()
        else:
            proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
    except OSError as exc:
        return {"ok": False, "message": f"Stop failed: {exc}"}
    _active["proc"] = None
    return {"ok": True, "message": "Stopped.", "gameId": _active.get("game_id") or ""}


def run_once(game: Game, runtime: Runtime) -> tuple[int, str, list[str], dict[str, Any]]:
    logs_dir().mkdir(parents=True, exist_ok=True)
    log_path = logs_dir() / f"{game.id}.log"
    cmd, env, warnings = build_launch_command(game, runtime)
    meta: dict[str, Any] = {"pid": None, "durationSec": 0, "cmd": cmd[:6]}
    started = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(_workdir(game)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        _active["proc"] = proc
        _active["game_id"] = game.id
        _active["started"] = started
        meta["pid"] = proc.pid
        stdout, stderr = proc.communicate()
        code = int(proc.returncode or 0)
        _active["proc"] = None
        meta["durationSec"] = int(time.time() - started)
        text = (stdout or "") + "\n" + (stderr or "")
        if warnings:
            text = "Moss: " + "; ".join(warnings) + "\n\n" + text
        log_path.write_text(text, encoding="utf-8", errors="replace")
        return code, text, warnings, meta
    except OSError as exc:
        _active["proc"] = None
        text = str(exc)
        log_path.write_text(text, encoding="utf-8")
        meta["durationSec"] = int(time.time() - started)
        return 1, text, warnings, meta


def apply_fix(game: Game, runtime: Runtime, match: RecipeMatch) -> str:
    if match.action == "winetricks" and match.verb:
        ok = run_verb(runtime, Path(game.prefix), match.verb)
        if ok and match.verb not in game.verbs:
            game.verbs.append(match.verb)
            upsert(game)
        return f"applied {match.verb}" if ok else f"failed to apply {match.verb}"
    return match.message or "stopped"


def apply_recipe_by_id(game: Game, recipe_id: str) -> dict[str, Any]:
    """Manually apply a known recipe (for Launch failed → Apply Fix)."""
    runtime = detect_runtime(game)
    if runtime is None:
        return {"ok": False, "message": "No Proton or Wine found."}
    recipes = load_recipes()
    recipe = next((r for r in recipes if r.get("id") == recipe_id), None)
    if not recipe:
        return {"ok": False, "message": f"Unknown recipe: {recipe_id}"}
    action = recipe.get("action", "report")
    if action == "report":
        return {"ok": False, "message": recipe.get("message") or "No automatic fix for this issue."}
    match = RecipeMatch(
        recipe_id=recipe_id,
        action="winetricks" if action in ("winetricks", "map_dll") else action,
        verb=recipe.get("verb"),
        message=recipe.get("message"),
    )
    if match.action != "winetricks" or not match.verb:
        return {"ok": False, "message": "Moss could not identify a safe automatic fix."}
    note = apply_fix(game, runtime, match)
    return {"ok": note.startswith("applied"), "message": note, "verb": match.verb}


def launch_game(game: Game, auto_fix: bool = True) -> dict:
    game = apply_profile(game)
    runtime = detect_runtime(game)
    create_prefix(game.id, runtime)
    if runtime is None:
        return {
            "ok": False,
            "log": "No Proton or Wine found.",
            "tried": [],
            "recipe_id": "",
            "anti_cheat": False,
            "message": "No Proton or Wine found.",
            "can_fix": False,
            "pid": None,
            "durationSec": 0,
        }
    game.prefix = str(create_prefix(game.id, runtime))
    # Persist last played on the stored game id
    stored = game
    from moss.store import get_game

    real = get_game(game.id) or game
    real.last_played = datetime.now(timezone.utc).isoformat(timespec="seconds")
    real.prefix = game.prefix
    upsert(real)
    ensure_components(real, runtime)
    game.prefix = real.prefix
    game.verbs = real.verbs

    if game.windows_version:
        apply_windows_version(runtime, Path(game.prefix), game.windows_version)

    tried: list[str] = []
    recipe_id = ""
    anti_cheat = False
    stop_message = ""
    can_fix = False
    code, log, warnings, meta = run_once(game, runtime)
    tried.extend(warnings)
    retries = 0
    while auto_fix and retries < MAX_RETRIES:
        match = match_log(log)
        if match is None:
            break
        recipe_id = match.recipe_id
        if match.action == "report":
            msg = match.message or match.recipe_id
            tried.append(msg)
            stop_message = msg
            if match.recipe_id in ANTICHEAT_RECIPES or "Anti-Cheat" in (match.message or ""):
                anti_cheat = True
            break
        if match.verb and match.verb in tried:
            break
        can_fix = True
        note = apply_fix(game, runtime, match)
        tried.append(note)
        retries += 1
        code, log, _, meta = run_once(game, runtime)

    # If we exited with a winetricks-able match that wasn't applied (report path), can_fix false
    if not can_fix and recipe_id and not anti_cheat:
        recipes = {r.get("id"): r for r in load_recipes()}
        r = recipes.get(recipe_id) or {}
        if r.get("action") == "winetricks" and r.get("verb"):
            can_fix = True
            stop_message = stop_message or f"Recommended: {r.get('verb')}"

    if not stop_message and code != 0:
        stop_message = "Moss could not identify a safe automatic fix." if not recipe_id else stop_message

    tail = "\n".join(log.splitlines()[-80:])
    return {
        "ok": code == 0,
        "code": code,
        "log": tail,
        "full_log": log,
        "tried": tried,
        "runner": runtime.as_dict(),
        "recipe_id": recipe_id,
        "anti_cheat": anti_cheat,
        "message": stop_message,
        "can_fix": can_fix and not anti_cheat,
        "pid": meta.get("pid"),
        "durationSec": meta.get("durationSec", 0),
    }
