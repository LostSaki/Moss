from moss.updatecheck import _newer, check_for_update


def test_newer() -> None:
    assert _newer("0.2.0", "0.1.0")
    assert not _newer("0.1.0", "0.1.0")
    assert not _newer("0.1.0", "0.2.0")
    assert _newer("v1.0.0", "0.9.0")


def test_check_no_crash() -> None:
    info = check_for_update("0.1.0")
    assert info.url
    assert isinstance(info.available, bool)
