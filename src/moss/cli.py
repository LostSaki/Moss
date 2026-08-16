from __future__ import annotations

import argparse
import sys
from pathlib import Path

from moss import __version__
from moss.artwork import fetch_artwork, search_steamgriddb
from moss.install import add_from_exe, add_from_folder, add_single_game_folder, install_setup
from moss.launch import launch_game
from moss.paths import ensure_dirs
from moss.runtime import detect_runtime
from moss.store import get_game, load_config, load_library, save_config


def main(argv: list[str] | None = None) -> int:
    ensure_dirs()
    parser = argparse.ArgumentParser(prog="moss", description="Moss — Windows games on Linux/SteamOS")
    parser.add_argument("--version", action="version", version=f"Moss {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Scan a folder for Windows games and add them")
    p_scan.add_argument("folder", type=Path)
    p_scan.add_argument(
        "--single",
        action="store_true",
        help="Treat the folder as one game (do not scan sibling titles)",
    )

    p_add = sub.add_parser("add", help="Add a single .exe")
    p_add.add_argument("exe", type=Path)
    p_add.add_argument("--name")

    p_install = sub.add_parser("install", help="Run a Windows setup.exe in a prefix")
    p_install.add_argument("setup", type=Path)
    p_install.add_argument("--name", required=True)

    p_launch = sub.add_parser("launch", help="Launch a library game")
    p_launch.add_argument("game_id")
    p_launch.add_argument("--no-fix", action="store_true")

    p_art = sub.add_parser("artwork", help="Fetch SteamGridDB / Steam artwork")
    p_art.add_argument("game_id")
    p_art.add_argument("--search")

    sub.add_parser("list", help="List library")
    sub.add_parser("ui", help="Open the native Moss window")

    p_cfg = sub.add_parser("config", help="Set config values")
    p_cfg.add_argument("--games-folder")
    p_cfg.add_argument("--steamgriddb-key")
    p_cfg.add_argument("--proton-path")

    args = parser.parse_args(argv)

    if args.cmd == "scan":
        if args.single:
            g = add_single_game_folder(args.folder)
            games = [g] if g else []
        else:
            games = add_from_folder(args.folder)
        if not games:
            print("No suitable .exe files found.")
            return 1
        for g in games:
            print(f"{g.id}\t{g.name}\t{g.exe}")
        return 0

    if args.cmd == "add":
        g = add_from_exe(args.exe, args.name)
        print(f"added {g.id}")
        return 0

    if args.cmd == "install":
        g = install_setup(args.setup, args.name)
        print(f"installed {g.id} exe={g.exe}")
        return 0

    if args.cmd == "launch":
        game = get_game(args.game_id)
        if not game:
            print(f"unknown game: {args.game_id}", file=sys.stderr)
            return 1
        result = launch_game(game, auto_fix=not args.no_fix)
        if result.get("tried"):
            print("tried:", "; ".join(result["tried"]))
        print(result.get("log") or "")
        return 0 if result.get("ok") else 1

    if args.cmd == "artwork":
        game = get_game(args.game_id)
        if not game:
            print(f"unknown game: {args.game_id}", file=sys.stderr)
            return 1
        cfg = load_config()
        key = cfg.get("steamgriddb_api_key") or ""
        if args.search and key:
            hits = search_steamgriddb(args.search, key)
            for h in hits[:8]:
                print(f"{h.get('id')}\t{h.get('name')}")
        fetch_artwork(game, args.search)
        print(game.artwork)
        return 0

    if args.cmd == "list":
        for g in load_library().values():
            print(f"{g.id}\t{g.name}\t{g.exe}")
        if not detect_runtime():
            print("(no Proton/Wine detected on this machine)", file=sys.stderr)
        return 0

    if args.cmd == "config":
        cfg = load_config()
        if args.games_folder:
            cfg["games_folder"] = args.games_folder
        if args.steamgriddb_key:
            cfg["steamgriddb_api_key"] = args.steamgriddb_key
        if args.proton_path:
            cfg["proton_path"] = args.proton_path
        save_config(cfg)
        print(cfg)
        return 0

    if args.cmd == "ui":
        from moss.ui.app import run_app

        return run_app()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
