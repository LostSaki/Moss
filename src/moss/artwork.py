from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from moss.paths import artwork_dir
from moss.store import Game, load_config, upsert

STEAMGRIDDB = "https://www.steamgriddb.com/api/v2"
STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"


def _download(url: str, dest: Path, headers: dict[str, str] | None = None) -> bool:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Moss/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _json(url: str, headers: dict[str, str] | None = None) -> dict | None:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Moss/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def search_steamgriddb(name: str, api_key: str) -> list[dict]:
    q = urllib.parse.quote(name)
    data = _json(
        f"{STEAMGRIDDB}/search/autocomplete/{q}",
        {"Authorization": f"Bearer {api_key}", "User-Agent": "Moss/0.1"},
    )
    if not data or not data.get("success"):
        return []
    return data.get("data") or []


def fetch_from_steamgriddb(game: Game, sgdb_id: int, api_key: str) -> Game:
    headers = {"Authorization": f"Bearer {api_key}", "User-Agent": "Moss/0.1"}
    dest_root = artwork_dir(game.id)
    kinds = {
        "grid": (f"{STEAMGRIDDB}/grids/game/{sgdb_id}?dimensions=600x900", "grid.png"),
        "hero": (f"{STEAMGRIDDB}/heroes/game/{sgdb_id}", "hero.png"),
        "logo": (f"{STEAMGRIDDB}/logos/game/{sgdb_id}", "logo.png"),
        "icon": (f"{STEAMGRIDDB}/icons/game/{sgdb_id}", "icon.png"),
    }
    for key, (url, filename) in kinds.items():
        listing = _json(url, headers)
        if not listing or not listing.get("data"):
            continue
        img_url = listing["data"][0].get("url")
        if not img_url:
            continue
        dest = dest_root / filename
        if _download(img_url, dest, headers):
            game.artwork[key] = str(dest)
    upsert(game)
    return game


def fetch_from_steam_store(game: Game, name: str) -> Game:
    q = urllib.parse.urlencode({"term": name, "l": "english", "cc": "US"})
    data = _json(f"{STEAM_SEARCH}?{q}")
    items = (data or {}).get("items") or []
    if not items:
        return game
    appid = items[0].get("id")
    if not appid:
        return game
    dest = artwork_dir(game.id) / "grid.jpg"
    url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900_2x.jpg"
    if _download(url, dest):
        game.artwork["grid"] = str(dest)
    hero = artwork_dir(game.id) / "hero.jpg"
    hurl = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_hero.jpg"
    if _download(hurl, hero):
        game.artwork["hero"] = str(hero)
    upsert(game)
    return game


def fetch_artwork(game: Game, search_name: str | None = None) -> Game:
    name = search_name or game.name
    cfg = load_config()
    key = (cfg.get("steamgriddb_api_key") or "").strip()
    if key:
        hits = search_steamgriddb(name, key)
        if hits:
            fetch_from_steamgriddb(game, hits[0]["id"], key)
    if "grid" not in game.artwork:
        fetch_from_steam_store(game, name)
    return game
