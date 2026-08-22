from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from moss.paths import config_path, ensure_dirs, library_path

WINDOWS_VERSIONS = ("", "win10", "win7", "winxp")


@dataclass
class Game:
    id: str
    name: str
    exe: str
    prefix: str
    verbs: list[str] = field(default_factory=list)
    artwork: dict[str, str] = field(default_factory=dict)
    steam_shortcut_id: int | None = None
    favorite: bool = False
    last_played: str = ""
    working_dir: str = ""
    launch_args: str = ""
    env_vars: dict[str, str] = field(default_factory=dict)
    runner_id: str = ""
    windows_version: str = ""
    dll_overrides: dict[str, str] = field(default_factory=dict)
    dxvk_enabled: bool = True
    vkd3d_enabled: bool = True
    gamescope_enabled: bool = False
    gamescope_args: str = ""
    mangohud_enabled: bool = False
    gamemode_enabled: bool = False
    esync_enabled: bool = True
    fsync_enabled: bool = True
    launch_profiles: list[dict] = field(default_factory=list)
    active_profile_id: str = ""

    def exe_path(self) -> Path:
        return Path(self.exe)

    def prefix_path(self) -> Path:
        return Path(self.prefix)

    def is_ready(self) -> bool:
        have = set(self.verbs)
        return "d3dcompiler_47" in have and ("vcrun2019" in have or "vcrun2022" in have)


def _parse_kv_map(raw: Any) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items() if str(k).strip()}
    if isinstance(raw, list):
        parsed: dict[str, str] = {}
        for entry in raw:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                parsed[str(entry[0]).strip()] = str(entry[1])
            elif isinstance(entry, str) and "=" in entry:
                k, _, v = entry.partition("=")
                if k.strip():
                    parsed[k.strip()] = v.strip()
        return parsed
    if isinstance(raw, str):
        parsed = {}
        for line in raw.splitlines():
            text = line.strip()
            if not text or text.startswith("#") or "=" not in text:
                continue
            k, _, v = text.partition("=")
            if k.strip():
                parsed[k.strip()] = v.strip()
        return parsed
    return {}


def _game_from_dict(item: dict[str, Any]) -> Game:
    allowed = {f.name for f in fields(Game)}
    data = {k: v for k, v in item.items() if k in allowed}
    data["env_vars"] = _parse_kv_map(data.get("env_vars"))
    data["dll_overrides"] = _parse_kv_map(data.get("dll_overrides"))
    win = str(data.get("windows_version") or "")
    if win and win not in WINDOWS_VERSIONS:
        data["windows_version"] = ""
    else:
        data["windows_version"] = win
    data.setdefault("runner_id", "")
    data.setdefault("working_dir", "")
    data.setdefault("launch_args", "")
    data.setdefault("dxvk_enabled", True)
    data.setdefault("vkd3d_enabled", True)
    data.setdefault("gamescope_enabled", False)
    data.setdefault("gamescope_args", "")
    data.setdefault("mangohud_enabled", False)
    data.setdefault("gamemode_enabled", False)
    data.setdefault("esync_enabled", True)
    data.setdefault("fsync_enabled", True)
    data.setdefault("launch_profiles", [])
    data.setdefault("active_profile_id", "")
    data["dxvk_enabled"] = bool(data.get("dxvk_enabled", True))
    data["vkd3d_enabled"] = bool(data.get("vkd3d_enabled", True))
    data["gamescope_enabled"] = bool(data.get("gamescope_enabled", False))
    data["mangohud_enabled"] = bool(data.get("mangohud_enabled", False))
    data["gamemode_enabled"] = bool(data.get("gamemode_enabled", False))
    data["esync_enabled"] = bool(data.get("esync_enabled", True))
    data["fsync_enabled"] = bool(data.get("fsync_enabled", True))
    data["gamescope_args"] = str(data.get("gamescope_args") or "")
    data["active_profile_id"] = str(data.get("active_profile_id") or "")
    profiles = data.get("launch_profiles") or []
    if isinstance(profiles, list):
        data["launch_profiles"] = [p for p in profiles if isinstance(p, dict)]
    else:
        data["launch_profiles"] = []
    return Game(**data)


def load_library() -> dict[str, Game]:
    ensure_dirs()
    path = library_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    games: dict[str, Game] = {}
    for item in raw.get("games", []):
        g = _game_from_dict(item)
        games[g.id] = g
    return games


def save_library(games: dict[str, Game]) -> None:
    ensure_dirs()
    payload = {"games": [asdict(g) for g in games.values()]}
    library_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def upsert(game: Game) -> Game:
    games = load_library()
    games[game.id] = game
    save_library(games)
    return game


def get_game(game_id: str) -> Game | None:
    return load_library().get(game_id)


def delete_game(game_id: str, remove_prefix: bool = False) -> None:
    games = load_library()
    game = games.pop(game_id, None)
    save_library(games)
    if remove_prefix and game:
        root = Path(game.prefix).parent
        shutil.rmtree(root, ignore_errors=True)


def default_config() -> dict[str, Any]:
    return {
        "games_folder": "",
        "steamgriddb_api_key": "",
        "proton_path": "",
        "wine_path": "",
        "preferred_runtime": "auto",  # auto | proton | wine
        "default_runtime_id": "",
        "check_updates": True,
        "update_channel": "stable",  # stable | beta
        "create_steam_shortcuts": True,
        "theme": "moss_dark",
        "glass_enabled": False,
        "onboarding_complete": False,
        "ai_suggestions_enabled": False,
        "ai_endpoint": "",
        "ai_api_key": "",
        "ai_model": "gpt-4o-mini",
    }


def load_config() -> dict[str, Any]:
    ensure_dirs()
    path = config_path()
    cfg = default_config()
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    merged = default_config()
    merged.update(cfg)
    config_path().write_text(json.dumps(merged, indent=2), encoding="utf-8")
