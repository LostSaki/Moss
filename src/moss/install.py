from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from moss.artwork import fetch_artwork
from moss.components import ensure_components
from moss.launch import run_once
from moss.prefix import create_prefix
from moss.runtime import detect_runtime
from moss.scan import display_name_from_path, pick_main_exe, scan_folder, slug_id
from moss.shortcuts import write_desktop, write_steam_shortcut
from moss.store import Game, get_game, load_config, load_library, upsert


@dataclass
class DiscoveredGame:
    """A scan hit before prefixes / artwork are created."""

    id: str
    name: str
    exe: str
    folder: str

    def as_dict(self) -> dict:
        return asdict(self)


def program_files_roots(prefix: Path) -> list[Path]:
    drive = prefix / "drive_c"
    return [
        drive / "Program Files",
        drive / "Program Files (x86)",
        drive / "users" / "steamuser" / "Desktop",
        drive / "users" / "steamuser" / "Downloads",
    ]


def find_installed_exe(prefix: Path, hint: str = "") -> Path | None:
    candidates = []
    for root in program_files_roots(prefix):
        if root.is_dir():
            candidates.extend(scan_folder(root))
    if hint:
        hint_l = hint.lower()
        candidates.sort(key=lambda f: (hint_l in f.path.stem.lower(), f.score), reverse=True)
    else:
        candidates.sort(key=lambda f: f.score, reverse=True)
    return candidates[0].path if candidates else None


def _finish_add(game: Game, name: str) -> Game:
    fetch_artwork(game, name)
    write_desktop(game)
    if load_config().get("create_steam_shortcuts", True):
        write_steam_shortcut(game)
    return game


def _title_from_folder(folder: Path) -> str:
    return folder.name.replace("_", " ").replace("-", " ").title()


def _existing_exe_paths() -> set[str]:
    out: set[str] = set()
    for g in load_library().values():
        try:
            out.add(str(Path(g.exe).resolve()))
        except OSError:
            out.add(str(Path(g.exe)))
    return out


def _is_duplicate(exe: Path, name: str, existing_exes: set[str] | None = None) -> bool:
    gid = slug_id(name)
    if get_game(gid):
        return True
    try:
        resolved = str(exe.resolve())
    except OSError:
        resolved = str(exe)
    known = existing_exes if existing_exes is not None else _existing_exe_paths()
    return resolved in known


def add_from_exe(exe: Path, name: str | None = None) -> Game:
    exe = Path(exe).resolve()
    name = name or display_name_from_path(exe)
    gid = slug_id(name)
    runtime = detect_runtime()
    prefix = create_prefix(gid, runtime)
    game = Game(id=gid, name=name, exe=str(exe), prefix=str(prefix))
    upsert(game)
    if runtime:
        ensure_components(game, runtime)
    return _finish_add(game, name)


def discover_games_in_library(root: Path) -> list[DiscoveredGame]:
    """Multi-game discovery: one candidate per child dir (+ root if it has its own exe)."""
    root = Path(root)
    if not root.is_dir():
        return []
    children = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
    targets: list[Path] = list(children)

    root_exe = pick_main_exe(root)
    if root_exe is not None:
        child_owned = False
        for child in children:
            try:
                root_exe.resolve().relative_to(child.resolve())
                child_owned = True
                break
            except ValueError:
                continue
        if not child_owned:
            targets = [root] + targets

    existing = _existing_exe_paths()
    found: list[DiscoveredGame] = []
    seen_ids: set[str] = set()
    for target in targets:
        exe = pick_main_exe(target)
        if exe is None:
            continue
        if target == root:
            name = display_name_from_path(exe)
        else:
            name = _title_from_folder(target)
        gid = slug_id(name)
        if gid in seen_ids or _is_duplicate(exe, name, existing):
            continue
        seen_ids.add(gid)
        found.append(
            DiscoveredGame(
                id=gid,
                name=name,
                exe=str(exe.resolve()),
                folder=str(target.resolve()),
            )
        )
    return found


def import_discovered(items: list[dict] | list[DiscoveredGame]) -> list[Game]:
    games: list[Game] = []
    for item in items:
        if isinstance(item, DiscoveredGame):
            exe = item.exe
            name = item.name
        else:
            exe = str(item.get("exe") or "")
            name = str(item.get("name") or "") or None
        if not exe:
            continue
        path = Path(exe)
        if not path.is_file():
            continue
        display = name or display_name_from_path(path)
        if _is_duplicate(path, display):
            continue
        games.append(add_from_exe(path, display))
    return games


def add_single_game_folder(folder: Path) -> Game | None:
    """Treat folder as exactly one game (do not scan sibling titles)."""
    folder = Path(folder)
    if folder.is_file() and folder.suffix.lower() == ".exe":
        if _is_duplicate(folder, display_name_from_path(folder)):
            return None
        return add_from_exe(folder)
    if not folder.is_dir():
        return None
    exe = pick_main_exe(folder)
    if exe is None:
        return None
    name = _title_from_folder(folder)
    if _is_duplicate(exe, name):
        return None
    return add_from_exe(exe, name=name)


def add_from_folder(folder: Path) -> list[Game]:
    """Import all discovered library games (CLI / bulk). Prefer discover + import for UI."""
    folder = Path(folder)
    if folder.is_file() and folder.suffix.lower() == ".exe":
        return [add_from_exe(folder)]
    discovered = discover_games_in_library(folder)
    if not discovered and folder.is_dir():
        g = add_single_game_folder(folder)
        return [g] if g else []
    return import_discovered(discovered)


def install_setup(setup_exe: Path, name: str) -> Game:
    setup_exe = Path(setup_exe).resolve()
    gid = slug_id(name)
    runtime = detect_runtime()
    prefix = create_prefix(gid, runtime)
    game = Game(id=gid, name=name, exe=str(setup_exe), prefix=str(prefix))
    upsert(game)
    if runtime:
        ensure_components(game, runtime)
        run_once(game, runtime)
    installed = find_installed_exe(prefix, hint=name)
    if installed:
        game.exe = str(installed)
        upsert(game)
    return _finish_add(game, name)
