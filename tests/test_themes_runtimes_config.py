from __future__ import annotations

import json
from pathlib import Path

import moss.runtime as runtime_mod
from moss.launch import _parse_args, _workdir
from moss.store import Game, default_config, load_config, load_library, save_config, upsert
from moss.themes import THEMES, list_themes, theme_tokens


def test_default_config_has_theme_keys() -> None:
    cfg = default_config()
    assert cfg["theme"] == "moss_dark"
    assert cfg["glass_enabled"] is False
    assert cfg["onboarding_complete"] is False
    assert cfg["preferred_runtime"] == "auto"


def test_theme_tokens_and_list() -> None:
    assert set(THEMES) == {"moss_dark", "high_contrast", "soft_glass"}
    assert theme_tokens("high_contrast")["background"] == "#000000"
    assert theme_tokens("missing")["accent"] == "#7FAF82"
    labels = {t["id"]: t["label"] for t in list_themes()}
    assert labels["soft_glass"] == "Soft Glass"


def test_game_new_fields_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    g = Game(
        id="demo",
        name="Demo",
        exe=str(tmp_path / "game.exe"),
        prefix=str(tmp_path / "pfx"),
        working_dir=str(tmp_path),
        launch_args="-windowed",
        env_vars={"FOO": "bar"},
        favorite=True,
    )
    upsert(g)
    loaded = load_library()["demo"]
    assert loaded.working_dir == str(tmp_path)
    assert loaded.launch_args == "-windowed"
    assert loaded.env_vars == {"FOO": "bar"}
    assert loaded.favorite is True


def test_game_from_legacy_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from moss.paths import ensure_dirs, library_path

    ensure_dirs()
    library_path().write_text(
        json.dumps(
            {
                "games": [
                    {
                        "id": "old",
                        "name": "Old",
                        "exe": "/tmp/a.exe",
                        "prefix": "/tmp/pfx",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    g = load_library()["old"]
    assert g.working_dir == ""
    assert g.launch_args == ""
    assert g.env_vars == {}


def test_config_persist_theme(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    save_config({"theme": "high_contrast", "glass_enabled": True, "onboarding_complete": True})
    cfg = load_config()
    assert cfg["theme"] == "high_contrast"
    assert cfg["glass_enabled"] is True
    assert cfg["onboarding_complete"] is True


def test_parse_args_and_workdir(tmp_path: Path) -> None:
    assert _parse_args('-windowed -name "My Game"') == ["-windowed", "-name", "My Game"]
    exe = tmp_path / "bin" / "game.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"MZ")
    g = Game(id="x", name="x", exe=str(exe), prefix=str(tmp_path / "p"))
    assert _workdir(g) == exe.parent
    g.working_dir = str(tmp_path)
    assert _workdir(g) == tmp_path


def test_list_runtimes_and_ge_status(monkeypatch, tmp_path: Path) -> None:
    import moss.runners.proton as proton_mod
    import moss.runners.wine as wine_mod

    monkeypatch.setattr(proton_mod, "steam_roots", lambda: [])
    monkeypatch.setattr(wine_mod, "discover_wine", lambda explicit="": [])
    assert runtime_mod.list_runtimes() == []
    status = runtime_mod.proton_ge_status()
    assert "message" in status
    assert "releases_url" in status


def test_list_proton_from_compat(monkeypatch, tmp_path: Path) -> None:
    import moss.runners.proton as proton_mod

    steam = tmp_path / "steam"
    compat = steam / "compatibilitytools.d" / "GE-Proton9-1"
    compat.mkdir(parents=True)
    (compat / "proton").write_text("#!/bin/sh\n", encoding="utf-8")
    (compat / "version").write_text("9.1\n", encoding="utf-8")
    monkeypatch.setattr(proton_mod, "steam_roots", lambda: [steam])
    found = runtime_mod.list_proton_runtimes()
    assert len(found) == 1
    assert found[0].name == "GE-Proton9-1"
    assert found[0].kind == "proton"
