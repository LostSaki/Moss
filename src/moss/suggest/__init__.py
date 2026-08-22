from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from moss.diagnose import match_log
from moss.gamesdb import match_game
from moss.paths import data_dir, ensure_dirs


@dataclass
class Suggestion:
    id: str
    title: str
    detail: str = ""
    action: str = "report"  # winetricks | report | change_exe | open_url
    verb: str = ""
    url: str = ""
    source: str = "rules"  # rules | ai

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SuggestContext:
    game_id: str = ""
    game_name: str = ""
    exe: str = ""
    runtime_name: str = ""
    log_excerpt: str = ""
    verbs_tried: list[str] = field(default_factory=list)
    db_id: str = ""
    db_notes: str = ""
    anti_cheat: str = "none"
    recipe_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SuggestContext:
        data = data or {}
        return cls(
            game_id=str(data.get("game_id") or ""),
            game_name=str(data.get("game_name") or ""),
            exe=str(data.get("exe") or ""),
            runtime_name=str(data.get("runtime_name") or ""),
            log_excerpt=str(data.get("log_excerpt") or ""),
            verbs_tried=list(data.get("verbs_tried") or []),
            db_id=str(data.get("db_id") or ""),
            db_notes=str(data.get("db_notes") or ""),
            anti_cheat=str(data.get("anti_cheat") or "none"),
            recipe_id=str(data.get("recipe_id") or ""),
        )


def _last_path() -> Path:
    return data_dir() / "last_suggest.json"


def save_suggest_context(ctx: SuggestContext) -> None:
    ensure_dirs()
    _last_path().write_text(json.dumps(ctx.as_dict(), indent=2), encoding="utf-8")


def load_suggest_context() -> SuggestContext | None:
    path = _last_path()
    if not path.exists():
        return None
    try:
        return SuggestContext.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None


def build_context(
    *,
    game_id: str = "",
    game_name: str = "",
    exe: str = "",
    runtime_name: str = "",
    log: str = "",
    verbs: list[str] | None = None,
    recipe_id: str = "",
) -> SuggestContext:
    entry = match_game(game_name, folder_name=Path(exe).parent.name if exe else "")
    excerpt = "\n".join((log or "").splitlines()[-80:])
    return SuggestContext(
        game_id=game_id,
        game_name=game_name,
        exe=exe,
        runtime_name=runtime_name,
        log_excerpt=excerpt,
        verbs_tried=list(verbs or []),
        db_id=entry.id if entry else "",
        db_notes=entry.notes if entry else "",
        anti_cheat=entry.anti_cheat if entry else "none",
        recipe_id=recipe_id,
    )


def redact_for_ai(ctx: SuggestContext) -> dict[str, Any]:
    """Strip directory paths to basenames for privacy-safe AI payloads."""
    exe_name = Path(ctx.exe).name if ctx.exe else ""
    lines = []
    for line in (ctx.log_excerpt or "").splitlines():
        # crude path scrub: keep last path segment after / or \
        scrubbed = line
        for sep in ("\\", "/"):
            if sep in scrubbed:
                parts = scrubbed.replace("\\", "/").split("/")
                scrubbed = parts[-1] if len(parts) > 1 and "." in parts[-1] else scrubbed
        lines.append(scrubbed)
    return {
        "game_name": ctx.game_name,
        "exe": exe_name,
        "runtime": ctx.runtime_name,
        "verbs_tried": ctx.verbs_tried,
        "db_id": ctx.db_id,
        "db_notes": ctx.db_notes,
        "anti_cheat": ctx.anti_cheat,
        "recipe_id": ctx.recipe_id,
        "log_excerpt": "\n".join(lines[-60:]),
    }


def suggest_fixes_rules(ctx: SuggestContext) -> list[Suggestion]:
    out: list[Suggestion] = []
    if ctx.anti_cheat in ("eac", "battleye"):
        out.append(
            Suggestion(
                id=f"anticheat-{ctx.anti_cheat}",
                title="Anti-cheat likely unsupported",
                detail=f"This title is marked as {ctx.anti_cheat.upper()} in the Moss games DB.",
                action="report",
                source="rules",
            )
        )
    if ctx.db_notes:
        out.append(
            Suggestion(
                id="db-notes",
                title="Notes from Moss games database",
                detail=ctx.db_notes,
                action="report",
                source="rules",
            )
        )
    match = match_log(ctx.log_excerpt or "")
    if match:
        if match.action == "winetricks" and match.verb:
            out.append(
                Suggestion(
                    id=f"recipe-{match.recipe_id}",
                    title=f"Install {match.verb}",
                    detail=match.message or f"Log matched recipe {match.recipe_id}.",
                    action="winetricks",
                    verb=match.verb or "",
                    source="rules",
                )
            )
        else:
            out.append(
                Suggestion(
                    id=f"recipe-{match.recipe_id}",
                    title=match.message or "See log for details",
                    detail=f"Matched recipe {match.recipe_id}.",
                    action="report",
                    source="rules",
                )
            )
    log_l = (ctx.log_excerpt or "").lower()
    if "vcruntime" in log_l or "msvcp" in log_l or "msvcr" in log_l:
        if not any(s.verb == "vcrun2019" for s in out):
            out.append(
                Suggestion(
                    id="hint-vcrun",
                    title="Install Visual C++ runtime (vcrun2019)",
                    detail="Log mentions MSVC runtime DLLs.",
                    action="winetricks",
                    verb="vcrun2019",
                    source="rules",
                )
            )
    if not out:
        out.append(
            Suggestion(
                id="check-exe",
                title="Confirm the game executable",
                detail="Moss may have picked a launcher or helper .exe. Use Change EXE if needed.",
                action="change_exe",
                source="rules",
            )
        )
    return out


def suggest_fixes(ctx: SuggestContext, *, use_ai: bool = False) -> list[Suggestion]:
    """Rule-based suggestions; optionally augment with AI (0.3.0)."""
    base = suggest_fixes_rules(ctx)
    if not use_ai:
        return base
    try:
        from moss.suggest.ai import suggest_fixes_ai

        ai_rows = suggest_fixes_ai(ctx)
        # Prefer AI rows that aren't duplicates by id
        seen = {s.id for s in base}
        for s in ai_rows:
            if s.id not in seen:
                base.append(s)
                seen.add(s.id)
    except Exception:
        pass
    return base
