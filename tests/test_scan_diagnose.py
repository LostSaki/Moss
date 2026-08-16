from pathlib import Path

from moss.diagnose import match_log
from moss.scan import pick_main_exe, should_skip_exe, slug_id


def test_skips_uninstallers(tmp_path: Path) -> None:
    junk = tmp_path / "uninstall.exe"
    junk.write_bytes(b"MZ")
    redist = tmp_path / "redist" / "vcredist.exe"
    redist.parent.mkdir()
    redist.write_bytes(b"MZ")
    good = tmp_path / "CoolGame" / "CoolGame.exe"
    good.parent.mkdir()
    good.write_bytes(b"MZ")
    assert should_skip_exe(junk)
    assert should_skip_exe(redist)
    assert not should_skip_exe(good)
    assert pick_main_exe(tmp_path) == good


def test_slug_id() -> None:
    assert slug_id("Hello World!") == "hello-world"


def test_vcrun_recipe() -> None:
    log = "0009:err:module:import_dll Library VCRUNTIME140.dll not found"
    m = match_log(log)
    assert m is not None
    assert m.verb == "vcrun2019"
    assert m.action == "winetricks"


def test_unknown_dll_stops() -> None:
    log = "0009:err:module:import_dll Library totallyfake.dll not found"
    m = match_log(log)
    assert m is not None
    assert m.action == "report"
    assert m.dll == "totallyfake.dll"


def test_eac_does_not_loop() -> None:
    log = "Easy Anti-Cheat failed SEC_E_INVALID_TOKEN"
    m = match_log(log)
    assert m is not None
    assert m.action == "report"
