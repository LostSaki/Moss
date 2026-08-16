from __future__ import annotations

from pathlib import Path

from moss.components import list_common_verbs
from moss.diagnose import match_log
from moss.launch import ANTICHEAT_RECIPES, build_launch_env, build_launch_command
from moss.store import Game
from moss.themes import AUTO_GLASS_THEMES, THEMES, list_themes, theme_tokens
from moss.wrappers import wrap_command


class _FakeRuntime:
    kind = "proton"
    binary = Path("/fake/proton")
    proton_root = Path("/fake/steam/steamapps/common/Proton")
    id = "fake"
    name = "Fake Proton"

    def as_dict(self):
        return {"id": self.id, "name": self.name, "kind": self.kind}


def test_expanded_themes() -> None:
    assert "moss_light" in THEMES
    assert "deep_forest" in THEMES
    assert "ember" in THEMES
    assert "mist" in THEMES
    assert theme_tokens("moss_light")["background"] == "#F4F5F2"
    assert theme_tokens("ember")["accent"] == "#D1A85A"
    assert float(theme_tokens("moss_dark")["glassOpacity"]) == 0.55
    assert AUTO_GLASS_THEMES == frozenset({"soft_glass", "mist"})
    ids = {t["id"] for t in list_themes()}
    assert ids == set(THEMES)


def test_dxvk_env_and_wrappers(monkeypatch, tmp_path: Path) -> None:
    exe = tmp_path / "game.exe"
    exe.write_bytes(b"MZ")
    g = Game(
        id="t",
        name="t",
        exe=str(exe),
        prefix=str(tmp_path / "pfx"),
        dxvk_enabled=True,
        vkd3d_enabled=False,
        gamescope_enabled=True,
        gamescope_args="-f",
        mangohud_enabled=True,
        gamemode_enabled=True,
    )
    rt = _FakeRuntime()
    env = build_launch_env(g, rt)  # type: ignore[arg-type]
    assert env.get("PROTON_USE_WINED3D") == "0"
    assert "d3d12=b" in env.get("WINEDLLOVERRIDES", "")

    monkeypatch.setattr("moss.wrappers.which", lambda name: f"/usr/bin/{name}")
    cmd, env2, warnings = build_launch_command(g, rt)  # type: ignore[arg-type]
    assert warnings == []
    assert cmd[0].endswith("gamemoderun")
    assert "gamescope" in cmd[1] or cmd[1].endswith("gamescope")
    assert env2.get("MANGOHUD") == "1"


def test_wrap_skips_missing_tools(monkeypatch) -> None:
    g = Game(id="t", name="t", exe="/x.exe", prefix="/p", gamescope_enabled=True, mangohud_enabled=True)
    monkeypatch.setattr("moss.wrappers.which", lambda name: None)
    cmd, env, warnings = wrap_command(g, ["/proton", "run", "/x.exe"], {})
    assert cmd == ["/proton", "run", "/x.exe"]
    assert len(warnings) >= 2
    assert "MANGOHUD" not in env


def test_anticheat_recipes() -> None:
    m = match_log("Easy Anti-Cheat failed to initialize")
    assert m is not None
    assert m.recipe_id in ANTICHEAT_RECIPES
    assert m.action == "report"
    m2 = match_log("BattlEye Service could not start")
    assert m2 is not None
    assert m2.recipe_id == "battleye_unsupported"


def test_winetricks_verb_list() -> None:
    verbs = list_common_verbs(["vcrun2019"])
    assert any(v["id"] == "vcrun2019" and v["installed"] for v in verbs)
    assert any(v["id"] == "dxvk" and not v["installed"] for v in verbs)


def test_game_launch_fields_roundtrip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from moss.store import load_library, upsert

    g = Game(
        id="demo2",
        name="Demo2",
        exe=str(tmp_path / "g.exe"),
        prefix=str(tmp_path / "pfx"),
        dxvk_enabled=False,
        gamescope_enabled=True,
        gamescope_args="-w 1280",
        mangohud_enabled=True,
    )
    upsert(g)
    loaded = load_library()["demo2"]
    assert loaded.dxvk_enabled is False
    assert loaded.gamescope_enabled is True
    assert loaded.gamescope_args == "-w 1280"
    assert loaded.mangohud_enabled is True
