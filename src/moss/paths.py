from __future__ import annotations

import os
from pathlib import Path


def _home() -> Path:
    return Path.home()


def data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", _home() / "AppData" / "Local"))
        return base / "Moss"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "moss"
    return _home() / ".local" / "share" / "moss"


def config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", _home() / "AppData" / "Roaming"))
        return base / "Moss"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "moss"
    return _home() / ".config" / "moss"


def prefixes_dir() -> Path:
    return data_dir() / "prefixes"


def artwork_dir(game_id: str | None = None) -> Path:
    root = data_dir() / "artwork"
    return root / game_id if game_id else root


def logs_dir() -> Path:
    return data_dir() / "logs"


def library_path() -> Path:
    return data_dir() / "library.json"


def config_path() -> Path:
    return config_dir() / "config.json"


def ensure_dirs() -> None:
    for p in (data_dir(), config_dir(), prefixes_dir(), artwork_dir(), logs_dir()):
        p.mkdir(parents=True, exist_ok=True)
