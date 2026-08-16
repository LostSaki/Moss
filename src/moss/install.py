from __future__ import annotations

from pathlib import Path

from moss.artwork import fetch_artwork
from moss.components import ensure_components
from moss.prefix import create_prefix
from moss.runtime import detect_runtime
from moss.scan import display_name_from_path, pick_main_exe, scan_folder, slug_id
from moss.shortcuts import write_desktop, write_steam_shortcut
from moss.store import Game, load_config, upsert
from moss.launch import run_once


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


def add_from_folder(folder: Path) -> list[Game]:
    folder = Path(folder)
    games: list[Game] = []
    # One library entry per immediate child that looks like a game, else the folder itself
    children = [p for p in folder.iterdir() if p.is_dir()] if folder.is_dir() else []
    targets = children or ([folder] if folder.is_dir() else [])
    for target in targets:
        exe = pick_main_exe(target)
        if exe is None:
            continue
        games.append(add_from_exe(exe, name=target.name.replace("_", " ").replace("-", " ").title()))
    if not games and folder.is_file() and folder.suffix.lower() == ".exe":
        games.append(add_from_exe(folder))
    return games


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
