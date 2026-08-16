from __future__ import annotations

import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from moss.components import ensure_components, run_verb
from moss.diagnose import RecipeMatch, match_log
from moss.paths import logs_dir
from moss.prefix import apply_windows_version, create_prefix, wine_env
from moss.runtime import Runtime, detect_runtime
from moss.store import Game, upsert
from moss.wrappers import wrap_command

MAX_RETRIES = 3

# Anti-cheat / hard-stop recipe ids surfaced in UI
ANTICHEAT_RECIPES = frozenset({"eac_unsupported", "battleye_unsupported"})


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
    # DXVK / VKD3D toggles via DLL overrides when not already set
    overrides_lower = {k.lower() for k in (game.dll_overrides or {})}
    if game.dxvk_enabled:
        for dll in ("d3d11", "d3d10", "d3d10core", "d3d10_1", "dxgi"):
            if dll not in overrides_lower:
                parts.append(f"{dll}=n,b")
    else:
        # Prefer Wine D3D when DXVK off
        pass
    if game.vkd3d_enabled:
        if "d3d12" not in overrides_lower:
            parts.append("d3d12=n,b")
    else:
        if "d3d12" not in overrides_lower:
            parts.append("d3d12=b")
    return ";".join(parts)


def build_launch_env(game: Game, runtime: Runtime) -> dict[str, str]:
    env = wine_env(runtime, Path(game.prefix))
    env["WINEDEBUG"] = "+err,+fixme"
    if not game.dxvk_enabled and runtime.kind == "proton":
        env["PROTON_USE_WINED3D"] = "1"
    elif game.dxvk_enabled and runtime.kind == "proton":
        env.pop("PROTON_USE_WINED3D", None)
        env["PROTON_USE_WINED3D"] = "0"
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


def run_once(game: Game, runtime: Runtime) -> tuple[int, str, list[str]]:
    logs_dir().mkdir(parents=True, exist_ok=True)
    log_path = logs_dir() / f"{game.id}.log"
    cmd, env, warnings = build_launch_command(game, runtime)
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            cwd=str(_workdir(game)),
            capture_output=True,
            text=True,
            timeout=None,
        )
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if warnings:
            text = "Moss: " + "; ".join(warnings) + "\n\n" + text
        log_path.write_text(text, encoding="utf-8", errors="replace")
        return proc.returncode, text, warnings
    except OSError as exc:
        text = str(exc)
        log_path.write_text(text, encoding="utf-8")
        return 1, text, warnings


def apply_fix(game: Game, runtime: Runtime, match: RecipeMatch) -> str:
    if match.action == "winetricks" and match.verb:
        ok = run_verb(runtime, Path(game.prefix), match.verb)
        if ok and match.verb not in game.verbs:
            game.verbs.append(match.verb)
            upsert(game)
        return f"applied {match.verb}" if ok else f"failed to apply {match.verb}"
    return match.message or "stopped"


def launch_game(game: Game, auto_fix: bool = True) -> dict:
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
        }
    game.prefix = str(create_prefix(game.id, runtime))
    game.last_played = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert(game)
    ensure_components(game, runtime)

    if game.windows_version:
        apply_windows_version(runtime, Path(game.prefix), game.windows_version)

    tried: list[str] = []
    recipe_id = ""
    anti_cheat = False
    stop_message = ""
    code, log, warnings = run_once(game, runtime)
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
        note = apply_fix(game, runtime, match)
        tried.append(note)
        retries += 1
        code, log, _ = run_once(game, runtime)

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
    }
