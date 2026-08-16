from __future__ import annotations

import subprocess
from pathlib import Path

from moss.prefix import wine_env
from moss.runtime import Runtime, detect_runtime, which_winetricks
from moss.store import Game, upsert

DEFAULT_VERBS = ("d3dcompiler_47", "vcrun2019")

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


def list_common_verbs(installed: list[str] | None = None) -> list[dict[str, object]]:
    have = set(installed or [])
    return [
        {"id": vid, "label": label, "installed": vid in have}
        for vid, label in COMMON_VERBS
    ]


def needed_verbs(game: Game) -> list[str]:
    have = set(game.verbs)
    return [v for v in DEFAULT_VERBS if v not in have]


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


def ensure_components(game: Game, runtime: Runtime | None = None) -> Game:
    runtime = runtime or detect_runtime()
    if runtime is None:
        return game
    prefix = Path(game.prefix)
    for verb in needed_verbs(game):
        ok = run_verb(runtime, prefix, verb)
        if ok and verb not in game.verbs:
            game.verbs.append(verb)
            upsert(game)
    return game
