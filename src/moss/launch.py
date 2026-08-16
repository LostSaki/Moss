from __future__ import annotations

import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from moss.components import ensure_components, run_verb
from moss.diagnose import RecipeMatch, match_log
from moss.paths import logs_dir
from moss.prefix import create_prefix, wine_env
from moss.runtime import Runtime, detect_runtime
from moss.store import Game, upsert

MAX_RETRIES = 3


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
    return ";".join(parts)


def build_launch_env(game: Game, runtime: Runtime) -> dict[str, str]:
    env = wine_env(runtime, Path(game.prefix))
    env["WINEDEBUG"] = "+err,+fixme"
    overrides = _dll_overrides_env(game)
    if overrides:
        existing = env.get("WINEDLLOVERRIDES", "")
        env["WINEDLLOVERRIDES"] = f"{existing};{overrides}".strip(";") if existing else overrides
    # windows_version is persisted; winecfg apply is not automatic yet
    if game.windows_version:
        env["MOSS_WINDOWS_VERSION"] = game.windows_version
    for key, value in (game.env_vars or {}).items():
        if key:
            env[str(key)] = str(value)
    return env


def run_once(game: Game, runtime: Runtime) -> tuple[int, str]:
    logs_dir().mkdir(parents=True, exist_ok=True)
    log_path = logs_dir() / f"{game.id}.log"
    env = build_launch_env(game, runtime)
    args = _parse_args(game.launch_args)
    try:
        proc = subprocess.run(
            _command(runtime, Path(game.exe), args),
            env=env,
            cwd=str(_workdir(game)),
            capture_output=True,
            text=True,
            timeout=None,
        )
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        log_path.write_text(text, encoding="utf-8", errors="replace")
        return proc.returncode, text
    except OSError as exc:
        text = str(exc)
        log_path.write_text(text, encoding="utf-8")
        return 1, text


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
        }
    game.prefix = str(create_prefix(game.id, runtime))
    game.last_played = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upsert(game)
    ensure_components(game, runtime)

    tried: list[str] = []
    code, log = run_once(game, runtime)
    retries = 0
    while auto_fix and retries < MAX_RETRIES:
        match = match_log(log)
        if match is None:
            break
        if match.action == "report":
            tried.append(match.message or match.recipe_id)
            break
        if match.verb and match.verb in tried:
            break
        note = apply_fix(game, runtime, match)
        tried.append(note)
        retries += 1
        code, log = run_once(game, runtime)

    tail = "\n".join(log.splitlines()[-80:])
    return {
        "ok": code == 0,
        "code": code,
        "log": tail,
        "full_log": log,
        "tried": tried,
        "runner": runtime.as_dict(),
    }
