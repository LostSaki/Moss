from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from moss.gamesdb import verbs_for_game
from moss.prefix import wine_env
from moss.runtime import Runtime, detect_runtime, which_winetricks
from moss.store import Game, upsert

DEFAULT_VERBS = ("d3dcompiler_47", "vcrun2019", "vcrun2022")

ProgressCb = Callable[[str], None]

# Curated common winetricks verbs for the browser UI
COMMON_VERBS: tuple[tuple[str, str], ...] = (
    ("vcrun2019", "Visual C++ 2015–2019"),
    ("vcrun2022", "Visual C++ 2022"),
    ("d3dcompiler_47", "D3D Compiler 47"),
    ("d3dx9", "Direct3D 9 extras"),
    ("dotnet48", ".NET Framework 4.8"),
    ("corefonts", "Core fonts"),
    ("faudio", "FAudio"),
    ("xact", "XACT / XAudio"),
    ("vkd3d", "VKD3D (winetricks)"),
    ("dxvk", "DXVK (winetricks)"),
)

VERB_LABELS = {vid: label for vid, label in COMMON_VERBS}


def list_common_verbs(installed: list[str] | None = None) -> list[dict[str, object]]:
    have = set(installed or [])
    return [
        {"id": vid, "label": label, "installed": vid in have}
        for vid, label in COMMON_VERBS
    ]


def needed_verbs(game: Game, planned: list[str] | None = None) -> list[str]:
    have = set(game.verbs)
    plan = planned
    if plan is None:
        _, plan = verbs_for_game(game.name, folder_name=Path(game.exe).parent.name)
    return [v for v in plan if v not in have]


def run_verb(runtime: Runtime, prefix: Path, verb: str) -> bool:
    tricks = which_winetricks()
    if tricks is None:
        return False
    env = wine_env(runtime, prefix)
    try:
        r = subprocess.run(
            [str(tricks), "-q", verb],
            env=env,
            check=False,
            timeout=600,
            capture_output=True,
            text=True,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_components(
    game: Game,
    runtime: Runtime | None = None,
    *,
    progress: ProgressCb | None = None,
    planned_verbs: list[str] | None = None,
) -> tuple[Game, dict]:
    """Install missing winetricks verbs. Returns (game, meta)."""
    runtime = runtime or detect_runtime()
    meta: dict = {
        "ok": True,
        "winetricks": which_winetricks() is not None,
        "installed": [],
        "failed": [],
        "skipped": [],
        "message": "",
        "db_id": "",
    }
    if runtime is None:
        meta["ok"] = False
        meta["message"] = "No Proton or Wine found."
        return game, meta

    entry, plan = verbs_for_game(game.name, folder_name=Path(game.exe).parent.name)
    if planned_verbs is not None:
        plan = planned_verbs
    if entry:
        meta["db_id"] = entry.id

    need = needed_verbs(game, plan)
    if not need:
        meta["message"] = "Components already installed."
        return game, meta

    if which_winetricks() is None:
        meta["ok"] = False
        meta["skipped"] = need
        meta["message"] = "Install winetricks to auto-install Windows components."
        if progress:
            progress(meta["message"])
        return game, meta

    prefix = Path(game.prefix)
    for verb in need:
        label = VERB_LABELS.get(verb, verb)
        if progress:
            progress(f"Installing {label}…")
        ok = run_verb(runtime, prefix, verb)
        if ok:
            meta["installed"].append(verb)
            if verb not in game.verbs:
                game.verbs.append(verb)
                upsert(game)
        else:
            meta["failed"].append(verb)
            meta["ok"] = False

    if meta["failed"]:
        meta["message"] = "Some Windows components failed to install."
    elif meta["installed"]:
        meta["message"] = f"Installed {len(meta['installed'])} component(s)."
    return game, meta
