from moss.shortcuts import steam_shortcut_id


def test_shortcut_id_stable() -> None:
    a = steam_shortcut_id(r"C:\Games\a.exe", "Moss")
    b = steam_shortcut_id(r"C:\Games\a.exe", "Moss")
    assert a == b
    assert a & 0x80000000
