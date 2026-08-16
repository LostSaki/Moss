from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any

from moss import __version__
from moss.runtime import list_runtimes
from moss.store import get_game, load_config
from moss.wrappers import detect_tools


_SECRET_KEYS = frozenset(
    {
        "steamgriddb_api_key",
        "api_key",
        "apikey",
        "password",
        "token",
        "secret",
        "authorization",
    }
)


def _redact_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in cfg.items():
        if k.lower() in _SECRET_KEYS or "key" in k.lower() and "path" not in k.lower():
            out[k] = "***" if v else ""
        else:
            out[k] = v
    return out


def build_debug_report(game_id: str = "") -> str:
    """Human-readable debug report; secrets redacted. Safe to copy."""
    lines: list[str] = []
    lines.append("=== Moss Debug Report ===")
    lines.append(f"Moss version: {__version__}")
    lines.append(f"Python: {sys.version.split()[0]}")
    lines.append(f"Platform: {platform.platform()}")
    lines.append(f"System: {platform.system()} {platform.release()}")
    lines.append(f"Machine: {platform.machine()}")
    lines.append(f"Processor: {platform.processor() or 'unknown'}")
    try:
        import PySide6

        lines.append(f"PySide6: {PySide6.__version__}")
    except Exception:
        lines.append("PySide6: unavailable")

    lines.append("")
    lines.append("--- Config (redacted) ---")
    cfg = _redact_cfg(load_config())
    for k in sorted(cfg):
        lines.append(f"{k}: {cfg[k]}")

    lines.append("")
    lines.append("--- Detected runners ---")
    runtimes = list_runtimes()
    if not runtimes:
        lines.append("(none)")
    for rt in runtimes:
        d = rt.as_dict() if hasattr(rt, "as_dict") else dict(rt)
        lines.append(f"- {d.get('name')} [{d.get('kind')}] id={d.get('id')} path={d.get('path')}")

    tools = detect_tools()
    lines.append("")
    lines.append("--- Host tools ---")
    lines.append(f"gamescope: {tools.gamescope}")
    lines.append(f"mangohud: {tools.mangohud}")
    lines.append(f"gamemode: {tools.gamemode}")

    if game_id:
        g = get_game(game_id)
        lines.append("")
        lines.append(f"--- Game: {game_id} ---")
        if g:
            lines.append(f"name: {g.name}")
            lines.append(f"exe: {g.exe}")
            lines.append(f"prefix: {g.prefix}")
            lines.append(f"runner_id: {g.runner_id or '(default)'}")
            lines.append(f"windows_version: {g.windows_version or 'default'}")
            lines.append(f"dxvk: {g.dxvk_enabled}  vkd3d: {g.vkd3d_enabled}")
            lines.append(f"esync: {getattr(g, 'esync_enabled', True)}  fsync: {getattr(g, 'fsync_enabled', True)}")
            lines.append(f"verbs: {', '.join(g.verbs) or '—'}")
            log_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Moss" / "logs" / f"{g.id}.log"
            from moss.paths import logs_dir

            lp = logs_dir() / f"{g.id}.log"
            if lp.exists():
                tail = lp.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
                lines.append("")
                lines.append("--- Recent log tail ---")
                lines.extend(tail)
            else:
                lines.append("log: (none)")
        else:
            lines.append("(game not found)")

    lines.append("")
    lines.append("=== End report ===")
    return "\n".join(lines)
