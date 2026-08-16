from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from moss.paths import data_dir, prefixes_dir
from moss.runtime import Runtime, detect_runtime
from moss.scan import slug_id


def prefix_for(game_id: str) -> Path:
    return prefixes_dir() / slug_id(game_id) / "pfx"


def prefix_root(game_id: str) -> Path:
    return prefixes_dir() / slug_id(game_id)


def wine_env(runtime: Runtime, prefix: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["WINEPREFIX"] = str(prefix)
    env["WINEDEBUG"] = "-all"
    if runtime.kind == "proton" and runtime.proton_root:
        env["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(
            runtime.proton_root.parent.parent.parent
            if (runtime.proton_root.parent / "common").exists()
            else Path.home() / ".steam" / "steam"
        )
        env["STEAM_COMPAT_DATA_PATH"] = str(prefix.parent)
        env["PROTON_LOG"] = "1"
    return env


def create_prefix(game_id: str, runtime: Runtime | None = None) -> Path:
    prefix = prefix_for(game_id)
    prefix.mkdir(parents=True, exist_ok=True)
    marker = prefix / ".moss-wineboot"
    if marker.exists():
        return prefix
    runtime = runtime or detect_runtime()
    if runtime is None:
        marker.write_text("no-runtime\n", encoding="utf-8")
        return prefix
    env = wine_env(runtime, prefix)
    try:
        if runtime.kind == "proton":
            subprocess.run(
                [str(runtime.binary), "run", "wineboot", "-u"],
                env=env,
                check=False,
                timeout=120,
            )
        else:
            subprocess.run(
                [str(runtime.binary), "wineboot", "-u"],
                env=env,
                check=False,
                timeout=120,
            )
    except (OSError, subprocess.TimeoutExpired):
        pass
    marker.write_text("ok\n", encoding="utf-8")
    return prefix


def prefix_info(game_id: str) -> dict[str, Any]:
    root = prefix_root(game_id)
    pfx = prefix_for(game_id)
    exists = pfx.exists()
    size = 0
    if exists:
        for path in pfx.rglob("*"):
            if path.is_file():
                try:
                    size += path.stat().st_size
                except OSError:
                    continue
    return {
        "gameId": game_id,
        "path": str(pfx),
        "root": str(root),
        "exists": exists,
        "sizeBytes": size,
        "canBackup": exists,
        "canDelete": root.exists(),
    }


def open_prefix_path(game_id: str) -> str:
    pfx = prefix_for(game_id)
    if not pfx.exists():
        pfx.mkdir(parents=True, exist_ok=True)
    return str(pfx)


def backup_prefix(game_id: str) -> dict[str, Any]:
    """Zip the prefix directory into Moss data/backups. Real but bounded."""
    pfx = prefix_for(game_id)
    if not pfx.exists():
        return {"ok": False, "message": "Prefix does not exist yet.", "path": ""}
    backups = data_dir() / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = backups / f"{slug_id(game_id)}-{stamp}.zip"
    try:
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in pfx.rglob("*"):
                if path.is_file():
                    zf.write(path, arcname=str(path.relative_to(pfx.parent)))
    except OSError as exc:
        return {"ok": False, "message": f"Backup failed: {exc}", "path": ""}
    return {"ok": True, "message": f"Backup saved to {dest}", "path": str(dest)}


def delete_prefix(game_id: str) -> dict[str, Any]:
    root = prefix_root(game_id)
    if not root.exists():
        return {"ok": False, "message": "No prefix folder to delete.", "path": ""}
    try:
        shutil.rmtree(root)
    except OSError as exc:
        return {"ok": False, "message": f"Delete failed: {exc}", "path": str(root)}
    return {"ok": True, "message": "Prefix deleted.", "path": str(root)}


# winecfg -v values
_WINVER_MAP = {
    "win10": "win10",
    "win7": "win7",
    "winxp": "winxp",
}


def apply_windows_version(runtime: Runtime | None, prefix: Path, version: str) -> dict[str, Any]:
    """Apply Windows version via winecfg -v. No-op on missing runtime / empty version."""
    ver = (version or "").strip()
    if not ver:
        return {"ok": True, "message": "Using default Windows version.", "skipped": True}
    if ver not in _WINVER_MAP:
        return {"ok": False, "message": f"Unknown Windows version: {ver}", "skipped": False}
    if os.name != "posix":
        return {
            "ok": False,
            "message": "Windows version apply requires Linux/SteamOS (winecfg).",
            "skipped": True,
        }
    if runtime is None:
        return {"ok": False, "message": "No runtime available for winecfg.", "skipped": True}
    mapped = _WINVER_MAP[ver]
    env = wine_env(runtime, prefix)
    try:
        if runtime.kind == "proton":
            cmd = [str(runtime.binary), "run", "winecfg", "-v", mapped]
        else:
            cmd = [str(runtime.binary), "winecfg", "-v", mapped]
        proc = subprocess.run(cmd, env=env, check=False, timeout=90, capture_output=True, text=True)
        if proc.returncode == 0:
            return {"ok": True, "message": f"Windows version set to {mapped}.", "skipped": False}
        detail = (proc.stderr or proc.stdout or "").strip()[-200:]
        return {
            "ok": False,
            "message": f"winecfg failed ({proc.returncode}). {detail}",
            "skipped": False,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": f"winecfg error: {exc}", "skipped": False}
