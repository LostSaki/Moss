from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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

    def exe_path(self) -> Path:
        return Path(self.exe)

    def prefix_path(self) -> Path:
        return Path(self.prefix)


def load_library() -> dict[str, Game]:
    ensure_dirs()
    path = library_path()
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    games: dict[str, Game] = {}
    for item in raw.get("games", []):
        g = Game(**item)
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


def default_config() -> dict[str, Any]:
    return {
        "games_folder": "",
        "steamgriddb_api_key": "",
        "proton_path": "",
        "wine_path": "",
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
