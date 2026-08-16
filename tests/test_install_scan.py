from pathlib import Path

from moss.install import (
    add_single_game_folder,
    discover_games_in_library,
    import_discovered,
)
from moss.store import load_library


def _iso_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))


def _stub_side_effects(monkeypatch) -> None:
    monkeypatch.setattr("moss.install.detect_runtime", lambda: None)
    monkeypatch.setattr("moss.install.fetch_artwork", lambda game, name: game)
    monkeypatch.setattr("moss.install.write_desktop", lambda game: None)
    monkeypatch.setattr("moss.install.write_steam_shortcut", lambda game: None)
    monkeypatch.setattr("moss.install.create_prefix", lambda gid, runtime: Path("/tmp/pfx") / gid)
    monkeypatch.setattr("moss.install.ensure_components", lambda game, runtime: None)


def _write_exe(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"MZ")
    return path


def test_discover_multi_child_games(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    lib = tmp_path / "Games"
    _write_exe(lib / "Alpha" / "Alpha.exe")
    _write_exe(lib / "Beta" / "Beta.exe")
    _write_exe(lib / "Alpha" / "uninstall.exe")
    found = discover_games_in_library(lib)
    assert {d.name for d in found} == {"Alpha", "Beta"}


def test_discover_skips_duplicates(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    lib = tmp_path / "Games"
    exe = _write_exe(lib / "Only" / "Only.exe")
    import_discovered([{"exe": str(exe), "name": "Only"}])
    assert len(load_library()) == 1
    found = discover_games_in_library(lib)
    assert found == []


def test_add_single_ignores_siblings(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    lib = tmp_path / "Games"
    _write_exe(lib / "One" / "One.exe")
    _write_exe(lib / "Two" / "Two.exe")
    g = add_single_game_folder(lib / "One")
    assert g is not None
    assert g.name == "One"
    assert len(load_library()) == 1


def test_single_folder_with_subdirs(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    game = tmp_path / "Cool Game"
    _write_exe(game / "bin" / "CoolGame.exe")
    (game / "extra").mkdir()
    g = add_single_game_folder(game)
    assert g is not None
    assert g.name == "Cool Game"


def test_discover_mixed_root_and_children(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    lib = tmp_path / "Mixed"
    _write_exe(lib / "RootGame.exe")
    _write_exe(lib / "Child" / "Child.exe")
    found = discover_games_in_library(lib)
    assert len(found) == 2


def test_discover_zero_games(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    from moss.paths import ensure_dirs

    ensure_dirs()
    empty = tmp_path / "Empty"
    empty.mkdir()
    (empty / "readme.txt").write_text("hi")
    assert discover_games_in_library(empty) == []
