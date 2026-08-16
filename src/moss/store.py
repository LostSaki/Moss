from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from moss.paths import config_path, ensure_dirs, library_path


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

    def exe_path(self) -> Path:
        return Path(self.exe)

    def prefix_path(self) -> Path:
        return Path(self.prefix)

    def is_ready(self) -> bool:
        return "vcrun2019" in self.verbs and "d3dcompiler_47" in self.verbs


def _game_from_dict(item: dict[str, Any]) -> Game:
    allowed = {f.name for f in fields(Game)}
    data = {k: v for k, v in item.items() if k in allowed}
    env = data.get("env_vars")
    if env is None:
        data["env_vars"] = {}
    elif isinstance(env, list):
        # tolerate [["KEY","VAL"], ...] or ["KEY=VAL", ...]
        parsed: dict[str, str] = {}
        for entry in env:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                parsed[str(entry[0])] = str(entry[1])
            elif isinstance(entry, str) and "=" in entry:
                k, _, v = entry.partition("=")
                parsed[k.strip()] = v.strip()
        data["env_vars"] = parsed
    elif not isinstance(env, dict):
        data["env_vars"] = {}
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
        "create_steam_shortcuts": True,
        "theme": "moss_dark",
        "glass_enabled": False,
        "onboarding_complete": False,
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
