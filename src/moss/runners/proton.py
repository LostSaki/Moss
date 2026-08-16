from __future__ import annotations

import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from moss.runners.base import Runner

GE_REPO_API = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
GE_RELEASES_URL = "https://github.com/GloriousEggroll/proton-ge-custom/releases"


def steam_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home / ".steam" / "steam",
        home / ".local" / "share" / "Steam",
        home / ".steam" / "root",
        Path(os.environ.get("STEAM_DIR", "")),
    ]
    if os.name == "nt":
        pf = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        candidates.append(Path(pf) / "Steam")
    return [p for p in candidates if p and p.exists()]


def compatibilitytools_dirs() -> list[Path]:
    dirs: list[Path] = []
    for steam in steam_roots():
        dirs.append(steam / "compatibilitytools.d")
    home = Path.home() / ".steam" / "root" / "compatibilitytools.d"
    if home not in dirs:
        dirs.append(home)
    return dirs


def writable_compat_dir() -> Path | None:
    if os.name == "nt":
        return None
    for d in compatibilitytools_dirs():
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".moss-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return d
        except OSError:
            continue
    return None


def proton_binary(root: Path) -> Path:
    if root.is_file():
        return root
    for name in ("proton", "proton.sh"):
        cand = root / name
        if cand.exists():
            return cand
    return root / "proton"


def _make_proton(root: Path, name: str | None = None) -> Runner | None:
    if not root.exists():
        return None
    bin_ = proton_binary(root)
    looks_valid = (
        bin_.exists()
        or (root / "version").exists()
        or (root / "compatibilitytool.vdf").exists()
    )
    if root.is_dir() and not looks_valid:
        try:
            if not any(root.iterdir()):
                return None
        except OSError:
            return None
        if not bin_.exists() and not (root / "proton").exists():
            return None
    label = name or root.name
    return Runner(
        kind="proton",
        binary=bin_ if bin_.exists() else root / "proton",
        proton_root=root if root.is_dir() else root.parent,
        name=label,
        path=str(root if root.is_dir() else root.parent),
    )


def discover_proton(explicit: str = "") -> list[Runner]:
    found: list[Runner] = []
    seen: set[str] = set()

    if explicit:
        p = Path(explicit)
        if p.exists():
            root = p if p.is_dir() else p.parent
            rt = _make_proton(root, name=root.name)
            if rt:
                found.append(rt)
                seen.add(rt.path)

    for steam in steam_roots():
        common = steam / "steamapps" / "common"
        if common.is_dir():
            for d in sorted(common.iterdir(), key=lambda x: x.name.lower()):
                if d.is_dir() and d.name.startswith("Proton"):
                    rt = _make_proton(d)
                    if rt and rt.path not in seen:
                        found.append(rt)
                        seen.add(rt.path)
        compat = steam / "compatibilitytools.d"
        if compat.is_dir():
            for d in sorted(compat.iterdir(), key=lambda x: x.name.lower(), reverse=True):
                if not d.is_dir():
                    continue
                rt = _make_proton(d)
                if rt and rt.path not in seen:
                    found.append(rt)
                    seen.add(rt.path)
    return found


def find_proton(explicit: str = "") -> Runner | None:
    items = discover_proton(explicit)
    return items[0] if items else None


def proton_ge_status() -> dict[str, Any]:
    writable = writable_compat_dir()
    return {
        "platform": "windows" if os.name == "nt" else "linux",
        "available": os.name != "nt",
        "can_install": writable is not None,
        "compat_dir": str(writable) if writable else "",
        "releases_url": GE_RELEASES_URL,
        "message": (
            "Proton-GE install is Linux-only. Detection of Windows Steam Proton folders is limited."
            if os.name == "nt"
            else (
                "Ready to download Proton-GE into Steam compatibilitytools.d."
                if writable
                else "No writable Steam compatibilitytools.d found. Create ~/.steam/steam/compatibilitytools.d and retry."
            )
        ),
    }


def _pick_ge_tarball_asset(assets: list[dict]) -> dict | None:
    for asset in assets:
        name = asset.get("name") or ""
        if name.endswith(".tar.gz") and "GE-Proton" in name:
            return asset
    for asset in assets:
        name = asset.get("name") or ""
        if name.endswith(".tar.gz"):
            return asset
    return None


def install_proton_ge() -> dict[str, Any]:
    status = proton_ge_status()
    if not status["available"]:
        return {"ok": False, "message": status["message"], "path": ""}
    dest_root = writable_compat_dir()
    if dest_root is None:
        return {"ok": False, "message": status["message"], "path": ""}

    req = urllib.request.Request(
        GE_REPO_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Moss-Launcher"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            release = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"Failed to query GitHub releases: {exc}", "path": ""}

    asset = _pick_ge_tarball_asset(release.get("assets") or [])
    if not asset or not asset.get("browser_download_url"):
        return {
            "ok": False,
            "message": f"No tarball asset found. Download manually: {GE_RELEASES_URL}",
            "path": "",
        }

    tag = release.get("tag_name") or "GE-Proton"
    url = asset["browser_download_url"]
    try:
        with tempfile.TemporaryDirectory(prefix="moss-ge-") as tmp:
            tarball = Path(tmp) / asset["name"]
            with urllib.request.urlopen(url, timeout=120) as resp, tarball.open("wb") as out:
                shutil.copyfileobj(resp, out)
            with tarfile.open(tarball, "r:gz") as tar:
                for member in tar.getmembers():
                    member_path = Path(dest_root) / member.name
                    if not str(member_path.resolve()).startswith(str(dest_root.resolve())):
                        return {"ok": False, "message": "Unsafe archive paths rejected.", "path": ""}
                tar.extractall(dest_root)
    except (urllib.error.URLError, OSError, tarfile.TarError, TimeoutError) as exc:
        return {"ok": False, "message": f"Install failed: {exc}", "path": ""}

    installed = dest_root / tag
    if not installed.exists():
        candidates = [
            d
            for d in dest_root.iterdir()
            if d.is_dir() and ("GE-Proton" in d.name or "Proton" in d.name)
        ]
        installed = max(candidates, key=lambda p: p.stat().st_mtime) if candidates else dest_root

    return {
        "ok": True,
        "message": f"Installed {tag} to {installed}",
        "path": str(installed),
        "tag": tag,
        "runner_id": f"proton:{installed}",
    }
