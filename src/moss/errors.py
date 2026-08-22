from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from moss.paths import data_dir, ensure_dirs

MAX_ERRORS = 50


def _errors_path() -> Path:
    return data_dir() / "errors.json"


def record_error(
    kind: str,
    message: str,
    *,
    game_id: str = "",
    detail: str = "",
) -> dict[str, Any]:
    """Append a structured error to the ring buffer."""
    ensure_dirs()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        "message": message,
        "gameId": game_id or "",
        "detail": (detail or "")[:4000],
    }
    rows = list_errors()
    rows.insert(0, entry)
    rows = rows[:MAX_ERRORS]
    _errors_path().write_text(json.dumps({"errors": rows}, indent=2), encoding="utf-8")
    return entry


def list_errors(limit: int = MAX_ERRORS) -> list[dict[str, Any]]:
    ensure_dirs()
    path = _errors_path()
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = raw.get("errors") or []
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict)][:limit]


def clear_errors() -> None:
    ensure_dirs()
    _errors_path().write_text(json.dumps({"errors": []}, indent=2), encoding="utf-8")
