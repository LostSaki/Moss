from __future__ import annotations

import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from moss import __version__
from moss.paths import data_dir, ensure_dirs
from moss.updatecheck import GITHUB_API, UpdateInfo, _fmt_ver, _get, _newer


def updates_dir() -> Path:
    ensure_dirs()
    p = data_dir() / "updates"
    p.mkdir(parents=True, exist_ok=True)
    (p / "previous").mkdir(parents=True, exist_ok=True)
    (p / "download").mkdir(parents=True, exist_ok=True)
    return p


def current_executable() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return None


def can_self_update() -> bool:
    return current_executable() is not None


def previous_backup_path() -> Path | None:
    exe = current_executable()
    if not exe:
        return None
    bak = updates_dir() / "previous" / exe.name
    return bak if bak.is_file() else None


def _pick_asset(assets: list[dict], *, channel_hint: str = "") -> dict | None:
    """Choose a release asset matching this frozen build."""
    exe = current_executable()
    if not exe:
        return None
    name = exe.name.lower()
    platform = sys.platform
    prefer: list[str] = []
    if platform.startswith("win"):
        prefer = [".exe", "windows"]
    elif "appimage" in name or name.endswith(".appimage"):
        prefer = [".appimage", "appimage"]
    else:
        prefer = ["linux", "x86_64"]

    scored: list[tuple[int, dict]] = []
    for a in assets:
        an = str(a.get("name") or "").lower()
        if not an:
            continue
        score = 0
        for p in prefer:
            if p in an:
                score += 2
        if platform.startswith("win") and an.endswith(".exe") and "setup" not in an:
            score += 3
        if platform.startswith("linux") and an.endswith(".appimage"):
            score += 3
        if platform.startswith("linux") and "linux" in an and not an.endswith((".deb", ".flatpak")):
            score += 2
        if score:
            scored.append((score, a))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]


def _get_list(url: str) -> list | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Moss-UpdateCheck"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def check_for_update(current: str | None = None, channel: str = "stable") -> UpdateInfo:
    """Stable = latest non-prerelease; beta = newest release including prereleases."""
    current = current or __version__
    cur_label = _fmt_ver(current)
    channel = (channel or "stable").lower()
    if channel == "beta":
        data = _get_list(f"{GITHUB_API}/releases?per_page=15")
        if data is None:
            return UpdateInfo(
                available=False,
                current=current,
                message="Couldn't reach GitHub · try again later",
                ok=False,
            )
        if not data:
            return UpdateInfo(
                available=False,
                current=current,
                message=f"You're up to date · {cur_label}",
                ok=True,
            )
        rel = data[0]
    else:
        data = _get(f"{GITHUB_API}/releases/latest")
        if data is None:
            return UpdateInfo(
                available=False,
                current=current,
                message="Couldn't reach GitHub · try again later",
                ok=False,
            )
        rel = data

    tag = str(rel.get("tag_name") or "")
    url = str(rel.get("html_url") or "")
    if not tag:
        return UpdateInfo(
            available=False,
            current=current,
            message="Couldn't reach GitHub · try again later",
            ok=False,
        )
    pre = bool(rel.get("prerelease"))
    if _newer(tag, current):
        ch = " (pre-release)" if pre else ""
        return UpdateInfo(
            available=True,
            latest=tag,
            current=current,
            url=url,
            message=f"Update available · {_fmt_ver(tag)}{ch} (you have {cur_label})",
            ok=True,
        )
    return UpdateInfo(
        available=False,
        latest=tag,
        current=current,
        url=url,
        message=f"You're up to date · {cur_label}",
        ok=True,
    )


def download_and_stage_update(channel: str = "stable") -> dict[str, Any]:
    """Download matching asset into updates/download. Does not replace yet."""
    if not can_self_update():
        return {
            "ok": False,
            "message": "In-app update only works for portable AppImage / binary builds.",
        }
    info = check_for_update(channel=channel)
    if not info.available or not info.latest:
        return {"ok": False, "message": info.message or "No update available."}

    # Fetch full release for assets
    tag = info.latest
    rel = _get(f"{GITHUB_API}/releases/tags/{tag}")
    if rel is None:
        # beta might need list scan
        rows = _get_list(f"{GITHUB_API}/releases?per_page=20") or []
        rel = next((r for r in rows if str(r.get("tag_name")) == tag), None)
    if not rel:
        return {"ok": False, "message": "Could not load release assets."}
    asset = _pick_asset(list(rel.get("assets") or []))
    if not asset:
        return {
            "ok": False,
            "message": "No matching download for this build. Open the release page instead.",
            "url": info.url,
        }
    url = asset.get("browser_download_url")
    name = str(asset.get("name") or "Moss-update")
    if not url:
        return {"ok": False, "message": "Asset URL missing."}
    dest = updates_dir() / "download" / name
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Moss-UpdateCheck"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as out:
            shutil.copyfileobj(resp, out)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        return {"ok": False, "message": f"Download failed: {exc}"}
    meta = {"tag": tag, "file": str(dest), "name": name, "url": info.url}
    (updates_dir() / "download" / "pending.json").write_text(json.dumps(meta), encoding="utf-8")
    return {"ok": True, "message": f"Downloaded {name}. Restart to apply.", **meta}


def apply_staged_update() -> dict[str, Any]:
    """Replace current frozen binary with staged download; keep previous for rollback."""
    exe = current_executable()
    if not exe:
        return {"ok": False, "message": "Not a portable build."}
    pending_path = updates_dir() / "download" / "pending.json"
    if not pending_path.is_file():
        return {"ok": False, "message": "No staged update. Download first."}
    try:
        meta = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "message": "Corrupt pending update metadata."}
    staged = Path(str(meta.get("file") or ""))
    if not staged.is_file():
        return {"ok": False, "message": "Staged file missing."}
    bak_dir = updates_dir() / "previous"
    bak = bak_dir / exe.name
    try:
        if bak.exists():
            bak.unlink()
        shutil.copy2(exe, bak)
        # On Windows, replacing running exe is hard — write beside and instruct restart via rename script
        tmp = exe.with_suffix(exe.suffix + ".new")
        if tmp.exists():
            tmp.unlink()
        shutil.copy2(staged, tmp)
        if sys.platform.startswith("win"):
            # Leave .new next to exe; user restarts — apply on next launch via try_finish_update
            (updates_dir() / "apply_on_restart").write_text(str(tmp), encoding="utf-8")
            return {
                "ok": True,
                "message": "Update ready. Restart Moss to finish applying.",
                "restart": True,
                "tag": meta.get("tag"),
            }
        # POSIX: replace atomically when possible
        os.replace(tmp, exe)
        try:
            exe.chmod(0o755)
        except OSError:
            pass
        pending_path.unlink(missing_ok=True)
        return {
            "ok": True,
            "message": f"Updated to {meta.get('tag')}. Restart Moss.",
            "restart": True,
            "tag": meta.get("tag"),
        }
    except OSError as exc:
        return {"ok": False, "message": f"Apply failed: {exc}"}


def try_finish_update() -> dict[str, Any] | None:
    """Called at startup to finish Windows .new swap if pending."""
    marker = updates_dir() / "apply_on_restart"
    if not marker.is_file():
        return None
    exe = current_executable()
    if not exe:
        return None
    try:
        new_path = Path(marker.read_text(encoding="utf-8").strip())
        if new_path.is_file():
            bak = updates_dir() / "previous" / exe.name
            if not bak.exists():
                shutil.copy2(exe, bak)
            os.replace(new_path, exe)
        marker.unlink(missing_ok=True)
        pending = updates_dir() / "download" / "pending.json"
        pending.unlink(missing_ok=True)
        return {"ok": True, "message": "Update applied."}
    except OSError as exc:
        return {"ok": False, "message": f"Could not finish update: {exc}"}


def rollback_previous() -> dict[str, Any]:
    exe = current_executable()
    bak = previous_backup_path()
    if not exe or not bak:
        return {"ok": False, "message": "No previous version to restore."}
    try:
        tmp = exe.with_suffix(exe.suffix + ".rollback")
        shutil.copy2(bak, tmp)
        if sys.platform.startswith("win"):
            (updates_dir() / "apply_on_restart").write_text(str(tmp), encoding="utf-8")
            return {"ok": True, "message": "Rollback ready. Restart Moss.", "restart": True}
        os.replace(tmp, exe)
        try:
            exe.chmod(0o755)
        except OSError:
            pass
        return {"ok": True, "message": "Restored previous version. Restart Moss.", "restart": True}
    except OSError as exc:
        return {"ok": False, "message": f"Rollback failed: {exc}"}
