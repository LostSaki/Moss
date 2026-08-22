from __future__ import annotations

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
    assert info.current == "0.1.0"
    assert info.message


def test_up_to_date_message(monkeypatch) -> None:
    def fake(url: str, *, timeout: float = 12):
        if url.endswith("/releases/latest"):
            return {"tag_name": "v0.2.0", "html_url": "https://example.com/r"}, ""
        return None, "unexpected"

    monkeypatch.setattr("moss.updatecheck._request_json", fake)
    info = check_for_update("0.2.0")
    assert info.available is False
    assert info.ok is True
    assert "up to date" in info.message.lower()
    assert "v0.2.0" in info.message


def test_update_available_message(monkeypatch) -> None:
    def fake(url: str, *, timeout: float = 12):
        if url.endswith("/releases/latest"):
            return {"tag_name": "v0.2.9", "html_url": "https://example.com/r"}, ""
        return None, "unexpected"

    monkeypatch.setattr("moss.updatecheck._request_json", fake)
    info = check_for_update("0.2.0")
    assert info.available is True
    assert "Update available" in info.message
    assert "v0.2.9" in info.message
    assert "v0.2.0" in info.message


def test_network_failure_message(monkeypatch) -> None:
    def fake(url: str, *, timeout: float = 12):
        return None, "network: timed out"

    monkeypatch.setattr("moss.updatecheck._request_json", fake)
    info = check_for_update("0.2.0")
    assert info.available is False
    assert info.ok is False
    assert "Couldn't reach GitHub" in info.message
    assert "timed out" in info.message
