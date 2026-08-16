from __future__ import annotations

import json
from pathlib import Path

import moss.runners.manager as manager
import moss.runners.proton as proton_mod
import moss.runners.wine as wine_mod
from moss.launch import build_launch_env, _dll_overrides_env
from moss.prefix import backup_prefix, delete_prefix, prefix_for, prefix_info
from moss.runners.base import Runner
from moss.store import Game, load_library, save_config, upsert
from moss.runtime import detect_runtime, list_runtimes


def _iso_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))


def test_discover_proton_mocked(monkeypatch, tmp_path: Path) -> None:
    steam = tmp_path / "steam"
    common = steam / "steamapps" / "common" / "Proton 9.0"
    common.mkdir(parents=True)
    (common / "proton").write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(proton_mod, "steam_roots", lambda: [steam])
    found = proton_mod.discover_proton()
    assert len(found) == 1
    assert found[0].kind == "proton"
    assert "Proton 9.0" in found[0].name


def test_manager_resolve_per_game(monkeypatch, tmp_path: Path) -> None:
    _iso_paths(tmp_path, monkeypatch)
    wine = Runner(kind="wine", binary=tmp_path / "wine", name="Wine", path=str(tmp_path / "wine"))
    proton = Runner(
        kind="proton",
        binary=tmp_path / "proton",
        proton_root=tmp_path / "GE",
        name="GE",
        path=str(tmp_path / "GE"),
    )
    (tmp_path / "wine").write_text("x", encoding="utf-8")
    (tmp_path / "GE").mkdir()
    (tmp_path / "proton").write_text("x", encoding="utf-8")

    monkeypatch.setattr(manager, "list_runners", lambda: [proton, wine])
    monkeypatch.setattr(manager, "detect_default", lambda: wine)

    g = Game(id="g", name="G", exe="e.exe", prefix="p", runner_id=proton.id)
    assert manager.resolve_for_game(g).id == proton.id
    assert manager.resolve_for_game(Game(id="h", name="H", exe="e", prefix="p")).id == wine.id


def test_game_migration_new_fields(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    from moss.paths import ensure_dirs, library_path

    ensure_dirs()
    library_path().write_text(
        json.dumps(
            {
                "games": [
                    {
                        "id": "legacy",
                        "name": "Legacy",
                        "exe": "/tmp/a.exe",
                        "prefix": "/tmp/pfx",
                        "dll_overrides": ["d3d11=n,b"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    g = load_library()["legacy"]
    assert g.runner_id == ""
    assert g.windows_version == ""
    assert g.dll_overrides == {"d3d11": "n,b"}
    assert g.working_dir == ""


def test_dll_overrides_env_and_launch_env(monkeypatch, tmp_path: Path) -> None:
    _iso_paths(tmp_path, monkeypatch)
    rt = Runner(kind="wine", binary=tmp_path / "wine", path=str(tmp_path / "wine"))
    g = Game(
        id="x",
        name="x",
        exe=str(tmp_path / "g.exe"),
        prefix=str(tmp_path / "pfx"),
        dll_overrides={"d3d11": "n,b", "dxgi": "n"},
        env_vars={"FOO": "1"},
        windows_version="win10",
    )
    assert "d3d11=n,b" in _dll_overrides_env(g)
    env = build_launch_env(g, rt)
    assert "d3d11=n,b" in env["WINEDLLOVERRIDES"]
    assert env["FOO"] == "1"
    assert env["MOSS_WINDOWS_VERSION"] == "win10"
    assert env["WINEPREFIX"] == str(tmp_path / "pfx")


def test_prefix_backup_and_delete(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    pfx = prefix_for("demo-game")
    pfx.mkdir(parents=True)
    (pfx / "drive_c").mkdir()
    (pfx / "drive_c" / "save.txt").write_text("ok", encoding="utf-8")
    info = prefix_info("demo-game")
    assert info["exists"] is True
    assert info["canBackup"] is True
    backed = backup_prefix("demo-game")
    assert backed["ok"] is True
    assert Path(backed["path"]).is_file()
    deleted = delete_prefix("demo-game")
    assert deleted["ok"] is True
    assert not pfx.exists()


def test_runtime_wrapper_list(monkeypatch) -> None:
    monkeypatch.setattr(proton_mod, "steam_roots", lambda: [])
    monkeypatch.setattr(wine_mod, "discover_wine", lambda explicit="": [])
    assert list_runtimes() == []
    assert detect_runtime() is None


def test_set_default_runner_persists(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    rt = Runner(kind="proton", binary=tmp_path / "p", proton_root=tmp_path / "P", path=str(tmp_path / "P"), name="P")
    monkeypatch.setattr(manager, "get_runner", lambda rid: rt if rid == rt.id else None)
    out = manager.set_default_runner(rt.id)
    assert out is not None
    from moss.store import load_config

    cfg = load_config()
    assert cfg["default_runtime_id"] == rt.id
    assert cfg["proton_path"] == rt.path


def test_upsert_runner_id(tmp_path: Path, monkeypatch) -> None:
    _iso_paths(tmp_path, monkeypatch)
    g = Game(id="r1", name="R", exe="e.exe", prefix="p", runner_id="proton:/tmp/GE")
    upsert(g)
    assert load_library()["r1"].runner_id == "proton:/tmp/GE"
