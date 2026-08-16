from __future__ import annotations

from pathlib import Path

from moss.debugreport import build_debug_report
from moss.launch import apply_profile, build_launch_env
from moss.store import Game
from moss.themes import theme_tokens


class _FakeRuntime:
    kind = "proton"
    binary = Path("/fake/proton")
    proton_root = Path("/fake/steam/steamapps/common/Proton")
    id = "fake"
    name = "Fake Proton"

    def as_dict(self):
        return {"id": self.id, "name": self.name, "kind": self.kind}


def test_glass_opacity_tokens() -> None:
    assert float(theme_tokens("moss_dark")["glassOpacity"]) == 0.55
    assert float(theme_tokens("soft_glass")["glassOpacity"]) <= 0.55
    assert float(theme_tokens("mist")["glassOpacity"]) <= 0.55
    assert "dialogGlassOpacity" in theme_tokens("moss_dark")


def test_esync_fsync_env() -> None:
    g = Game(
        id="t",
        name="t",
        exe="/x.exe",
        prefix="/p",
        esync_enabled=False,
        fsync_enabled=True,
    )
    env = build_launch_env(g, _FakeRuntime())  # type: ignore[arg-type]
    assert env.get("WINEESYNC") == "0"
    assert env.get("WINEFSYNC") == "1"


def test_launch_profile_override() -> None:
    g = Game(
        id="t",
        name="t",
        exe="/x.exe",
        prefix="/p",
        launch_args="-default",
        runner_id="",
        env_vars={"A": "1"},
        launch_profiles=[
            {
                "id": "perf",
                "name": "Perf",
                "launch_args": "-high",
                "runner_id": "ge",
                "env_vars": {"B": "2"},
            }
        ],
        active_profile_id="perf",
    )
    applied = apply_profile(g)
    assert applied.launch_args == "-high"
    assert applied.runner_id == "ge"
    assert applied.env_vars.get("A") == "1"
    assert applied.env_vars.get("B") == "2"


def test_debug_report_redacts_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "la"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    from moss.store import save_config

    save_config({"steamgriddb_api_key": "SECRET_KEY_VALUE"})
    report = build_debug_report()
    assert "SECRET_KEY_VALUE" not in report
    assert "steamgriddb_api_key: ***" in report or "***" in report
    assert "Moss version:" in report
