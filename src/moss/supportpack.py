from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from moss.debugreport import build_debug_report
from moss.errors import list_errors
from moss.paths import data_dir, ensure_dirs, logs_dir
from moss.suggest import load_suggest_context


def export_support_pack(dest: Path, game_id: str = "") -> dict[str, Any]:
    """Write a zip support pack. Returns {ok, path, message}."""
    ensure_dirs()
    dest = Path(dest)
    if dest.is_dir():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        dest = dest / f"moss-support-{stamp}.zip"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("debug-report.txt", build_debug_report(game_id or ""))
            zf.writestr("errors.json", json.dumps({"errors": list_errors()}, indent=2))
            ctx = load_suggest_context()
            if ctx:
                zf.writestr("last-suggest.json", json.dumps(ctx.as_dict(), indent=2))
            # Attach up to 5 most recent logs
            logs = sorted(logs_dir().glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
            for path in logs[:5]:
                try:
                    zf.write(path, arcname=f"logs/{path.name}")
                except OSError:
                    continue
            if game_id:
                glog = logs_dir() / f"{game_id}.log"
                if glog.is_file() and glog.name not in {p.name for p in logs[:5]}:
                    try:
                        zf.write(glog, arcname=f"logs/{glog.name}")
                    except OSError:
                        pass
        return {"ok": True, "path": str(dest), "message": f"Support pack saved to {dest}"}
    except OSError as exc:
        return {"ok": False, "path": "", "message": f"Export failed: {exc}"}


def default_support_pack_path() -> Path:
    return data_dir() / "support-packs"
