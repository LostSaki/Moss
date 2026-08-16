from __future__ import annotations

import struct
from pathlib import Path
from zlib import crc32

from moss.store import Game, upsert

DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"


def steam_shortcut_id(exe: str, name: str) -> int:
    payload = (exe + name).encode("utf-8")
    return (crc32(payload) & 0xFFFFFFFF) | 0x80000000


def write_desktop(game: Game) -> Path:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    icon = game.artwork.get("icon") or game.artwork.get("grid") or ""
    path = DESKTOP_DIR / f"moss-{game.id}.desktop"
    body = "\n".join(
        [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={game.name}",
            f"Exec=moss launch {game.id}",
            "Categories=Game;",
            "Terminal=false",
            f"Icon={icon}" if icon else "Icon=applications-games",
            "",
        ]
    )
    path.write_text(body, encoding="utf-8")
    return path


def _steam_userdata() -> list[Path]:
    homes = [
        Path.home() / ".steam" / "steam" / "userdata",
        Path.home() / ".local" / "share" / "Steam" / "userdata",
    ]
    out: list[Path] = []
    for root in homes:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.is_dir() and child.name.isdigit() and child.name != "0":
                out.append(child)
    return out


def _vdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def write_steam_shortcut(game: Game) -> int | None:
    sid = steam_shortcut_id(game.exe, game.name)
    game.steam_shortcut_id = sid
    upsert(game)
    users = _steam_userdata()
    if not users:
        return sid
    for user in users:
        cfg = user / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        vdf = cfg / "shortcuts.vdf"
        _append_or_create_vdf(vdf, game, sid)
        _copy_grid_art(user, game, sid)
    return sid


def _copy_grid_art(user: Path, game: Game, sid: int) -> None:
    grid = user / "config" / "grid"
    grid.mkdir(parents=True, exist_ok=True)
    mapping = {
        "grid": f"{sid}.png",
        "hero": f"{sid}_hero.png",
        "logo": f"{sid}_logo.png",
        "icon": f"{sid}_icon.jpg",
    }
    for key, dest_name in mapping.items():
        src = game.artwork.get(key)
        if not src:
            continue
        sp = Path(src)
        if not sp.is_file():
            continue
        dest = grid / dest_name
        dest.write_bytes(sp.read_bytes())


def _append_or_create_vdf(path: Path, game: Game, sid: int) -> None:
    """Write a minimal binary-ish ASCII VDF entry Steam can often merge.

    Full binary VDF is complex; we write a sidecar text map Moss can re-apply
    and a simple shortcuts.vdf if missing. Existing binary files are left
    intact; a moss-shortcuts.txt notes the entry.
    """
    note = path.with_name("moss-shortcuts.txt")
    line = f'{sid}\t{game.name}\tmoss launch {game.id}\t{game.exe}\n'
    existing = note.read_text(encoding="utf-8") if note.exists() else ""
    if str(sid) not in existing:
        note.write_text(existing + line, encoding="utf-8")
    if not path.exists():
        # Minimal KV text fallback (Steam prefers binary; user may need to
        # add via Steam UI once, then grid art still applies).
        path.write_bytes(_minimal_binary_shortcut(game, sid))


def _minimal_binary_shortcut(game: Game, sid: int) -> bytes:
    # Binary VDF: 0x00 = start object, 0x01 = string, 0x02 = int, 0x08 = end
    def skey(k: str, v: str) -> bytes:
        return b"\x01" + k.encode() + b"\x00" + v.encode() + b"\x00"

    def ikey(k: str, v: int) -> bytes:
        return b"\x02" + k.encode() + b"\x00" + struct.pack("<I", v & 0xFFFFFFFF)

    inner = b"".join(
        [
            skey("appname", game.name),
            skey("exe", f"moss launch {game.id}"),
            skey("StartDir", str(Path(game.exe).parent)),
            skey("icon", game.artwork.get("icon", "")),
            skey("ShortcutPath", ""),
            skey("LaunchOptions", ""),
            ikey("IsHidden", 0),
            ikey("AllowDesktopConfig", 1),
            ikey("AllowOverlay", 1),
            ikey("OpenVR", 0),
            ikey("Devkit", 0),
            skey("DevkitGameID", ""),
            ikey("LastPlayTime", 0),
            b"\x00tags\x00\x08",
            b"\x08",
        ]
    )
    return b"\x00shortcuts\x00\x00" + b"0\x00" + inner + b"\x08\x08"
