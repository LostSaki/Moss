from __future__ import annotations

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


def _command(runtime: Runtime, exe: Path) -> list[str]:
    if runtime.kind == "proton":
        return [str(runtime.binary), "run", str(exe)]
    return [str(runtime.binary), str(exe)]


def run_once(game: Game, runtime: Runtime) -> tuple[int, str]:
    logs_dir().mkdir(parents=True, exist_ok=True)
    log_path = logs_dir() / f"{game.id}.log"
    env = wine_env(runtime, Path(game.prefix))
    env["WINEDEBUG"] = "+err,+fixme"
    try:
        proc = subprocess.run(
            _command(runtime, Path(game.exe)),
            env=env,
            cwd=str(Path(game.exe).parent),
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
    runtime = detect_runtime()
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
    }
