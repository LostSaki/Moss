"""Back-compat runtime API — discovery lives in moss.runners."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from moss.runners.base import Runner, Runtime
from moss.runners.manager import (
    detect_default,
    get_runner,
    list_runners,
    resolve_for_game,
    set_default_runner,
)
from moss.runners.manager import after_ge_install
from moss.runners.proton import (
    compatibilitytools_dirs,
    discover_proton,
    find_proton,
    install_proton_ge as _install_proton_ge,
    proton_binary,
    proton_ge_status,
    steam_roots,
    writable_compat_dir,
)
from moss.runners.wine import discover_wine, find_wine


def _steam_roots() -> list[Path]:
    return steam_roots()


def _proton_binary(root: Path) -> Path:
    return proton_binary(root)


def list_proton_runtimes() -> list[Runtime]:
    return discover_proton()


def list_wine_runtimes() -> list[Runtime]:
    return discover_wine()


def list_runtimes() -> list[Runtime]:
    return list_runners()


def detect_runtime(game=None) -> Runtime | None:
    if game is not None:
        return resolve_for_game(game)
    return detect_default()


def set_default_runtime(runtime_id: str) -> dict[str, str] | None:
    return set_default_runner(runtime_id)


def which_winetricks() -> Path | None:
    w = shutil.which("winetricks") or shutil.which("protontricks")
    return Path(w) if w else None


def install_proton_ge() -> dict[str, Any]:
    return after_ge_install(_install_proton_ge())


__all__ = [
    "Runtime",
    "Runner",
    "list_runtimes",
    "list_proton_runtimes",
    "list_wine_runtimes",
    "find_proton",
    "find_wine",
    "detect_runtime",
    "set_default_runtime",
    "which_winetricks",
    "proton_ge_status",
    "install_proton_ge",
    "compatibilitytools_dirs",
    "writable_compat_dir",
    "get_runner",
    "resolve_for_game",
]
