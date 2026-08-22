from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from moss.scan import slug_id


@dataclass
class GameDbEntry:
    id: str
    names: list[str] = field(default_factory=list)
    steam_appid: int = 0
    required_verbs: list[str] = field(default_factory=list)
    notes: str = ""
    anti_cheat: str = "none"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "names": list(self.names),
            "steam_appid": self.steam_appid,
            "required_verbs": list(self.required_verbs),
            "notes": self.notes,
            "anti_cheat": self.anti_cheat,
        }


def _db_path() -> Path:
    try:
        ref = resources.files("moss.data").joinpath("games_db.yaml")
        with resources.as_file(ref) as path:
            return Path(path)
    except (FileNotFoundError, ModuleNotFoundError, TypeError, AttributeError, OSError):
        return Path(__file__).resolve().parent / "data" / "games_db.yaml"


@lru_cache(maxsize=1)
def load_games_db() -> tuple[GameDbEntry, ...]:
    path = _db_path()
    if not path.is_file():
        return ()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries: list[GameDbEntry] = []
    for item in raw.get("games") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        names = [str(n) for n in (item.get("names") or []) if str(n).strip()]
        verbs = [str(v).strip() for v in (item.get("required_verbs") or []) if str(v).strip()]
        appid = item.get("steam_appid") or 0
        try:
            appid_i = int(appid)
        except (TypeError, ValueError):
            appid_i = 0
        entries.append(
            GameDbEntry(
                id=str(item["id"]),
                names=names,
                steam_appid=appid_i,
                required_verbs=verbs,
                notes=str(item.get("notes") or ""),
                anti_cheat=str(item.get("anti_cheat") or "none").lower(),
            )
        )
    return tuple(entries)


def _norm(text: str) -> str:
    return slug_id(text or "").replace("-", "")


def match_game(
    name: str = "",
    *,
    steam_appid: int | None = None,
    folder_name: str = "",
) -> GameDbEntry | None:
    """Best-effort match by Steam appid, then exact/slug name aliases."""
    entries = load_games_db()
    if steam_appid:
        for e in entries:
            if e.steam_appid and e.steam_appid == int(steam_appid):
                return e

    candidates = [n for n in (name, folder_name) if n]
    norms = {_norm(c) for c in candidates}
    slugs = {slug_id(c) for c in candidates}

    for e in entries:
        aliases = [e.id, *e.names]
        alias_slugs = {slug_id(a) for a in aliases}
        alias_norms = {_norm(a) for a in aliases}
        if slugs & alias_slugs or norms & alias_norms:
            return e

    best: GameDbEntry | None = None
    best_len = 0
    for e in entries:
        for alias in e.names:
            an = _norm(alias)
            if len(an) < 4:
                continue
            for c in norms:
                if an in c or c in an:
                    if len(an) > best_len:
                        best = e
                        best_len = len(an)
    return best


def verbs_for_game(
    name: str = "",
    *,
    steam_appid: int | None = None,
    folder_name: str = "",
    defaults: tuple[str, ...] | list[str] | None = None,
) -> tuple[GameDbEntry | None, list[str]]:
    from moss.components import DEFAULT_VERBS

    entry = match_game(name, steam_appid=steam_appid, folder_name=folder_name)
    base = list(defaults if defaults is not None else DEFAULT_VERBS)
    extra = list(entry.required_verbs) if entry else []
    seen: set[str] = set()
    out: list[str] = []
    for v in base + extra:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return entry, out
