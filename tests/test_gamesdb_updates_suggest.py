from pathlib import Path

from moss.gamesdb import match_game, verbs_for_game
from moss.suggest import SuggestContext, suggest_fixes_rules
from moss.updater import check_for_update


def test_match_hollow_knight() -> None:
    e = match_game("Hollow Knight")
    assert e is not None
    assert e.id == "hollow-knight"
    assert "vcrun2019" in e.required_verbs


def test_verbs_merge_defaults() -> None:
    entry, verbs = verbs_for_game("Celeste")
    assert entry is not None
    assert "d3dcompiler_47" in verbs
    assert "vcrun2019" in verbs
    assert "vcrun2022" in verbs  # from defaults


def test_suggest_vcrun_from_log() -> None:
    ctx = SuggestContext(
        game_name="Test",
        log_excerpt="0009:err:module:import_dll Library VCRUNTIME140.dll not found",
    )
    tips = suggest_fixes_rules(ctx)
    assert any(t.action == "winetricks" and t.verb == "vcrun2019" for t in tips)


def test_suggest_anticheat_from_db() -> None:
    ctx = SuggestContext(game_name="Elden Ring", anti_cheat="eac", db_id="elden-ring")
    # populate anti_cheat via match path
    from moss.gamesdb import match_game

    e = match_game("Elden Ring")
    assert e and e.anti_cheat == "eac"
    ctx = SuggestContext(game_name="Elden Ring", anti_cheat=e.anti_cheat, db_notes=e.notes)
    tips = suggest_fixes_rules(ctx)
    assert any("anti-cheat" in t.title.lower() or "anticheat" in t.id for t in tips)


def test_update_channel_stable_mock(monkeypatch) -> None:
    monkeypatch.setattr(
        "moss.updater._get",
        lambda url: {"tag_name": "v0.2.8", "prerelease": False, "html_url": "https://example.com"},
    )
    info = check_for_update("0.2.2", channel="stable")
    assert info.available is True
    assert "0.2.8" in info.latest


def test_update_channel_beta_prefers_prerelease(monkeypatch) -> None:
    monkeypatch.setattr(
        "moss.updater._get_list",
        lambda url: [
            {"tag_name": "v0.2.8", "prerelease": True, "html_url": "https://example.com/pre"},
            {"tag_name": "v0.2.2", "prerelease": False, "html_url": "https://example.com"},
        ],
    )
    info = check_for_update("0.2.2", channel="beta")
    assert info.available is True
    assert info.latest == "v0.2.8"
