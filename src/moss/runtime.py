from __future__ import annotations

import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from moss.store import load_config, save_config

GE_REPO_API = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest"
GE_RELEASES_URL = "https://github.com/GloriousEggroll/proton-ge-custom/releases"


@dataclass
class Runtime:
    kind: str  # proton | wine
    binary: Path
    proton_root: Path | None = None
    name: str = ""
    path: str = ""
    id: str = ""

    def as_dict(self) -> dict[str, str]:
        root = self.proton_root or self.binary
        return {
            "id": self.id or f"{self.kind}:{root}",
            "name": self.name or root.name,
            "kind": self.kind,
            "path": str(root),
            "binary": str(self.binary),
        }


def _steam_roots() -> list[Path]:
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
    for steam in _steam_roots():
        d = steam / "compatibilitytools.d"
        dirs.append(d)
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


def _proton_binary(root: Path) -> Path:
    if root.is_file():
        return root
    for name in ("proton", "proton.sh"):
        cand = root / name
        if cand.exists():
            return cand
    return root / "proton"


def _make_proton(root: Path, name: str | None = None) -> Runtime | None:
    bin_ = _proton_binary(root)
    if not bin_.exists() and not (root / "proton").exists() and not (root / "version").exists():
        # accept folders that look like Proton even if binary check is soft
        if not root.is_dir() or not any(root.iterdir()):
            return None
    label = name or root.name
    rid = f"proton:{root}"
    return Runtime(
        kind="proton",
        binary=bin_ if bin_.exists() else root / "proton",
        proton_root=root if root.is_dir() else root.parent,
        name=label,
        path=str(root),
        id=rid,
    )


def list_proton_runtimes() -> list[Runtime]:
    found: list[Runtime] = []
    seen: set[str] = set()
    for steam in _steam_roots():
        common = steam / "steamapps" / "common"
        if common.is_dir():
            for d in sorted(common.iterdir(), key=lambda p: p.name.lower()):
                if d.is_dir() and d.name.startswith("Proton"):
                    rt = _make_proton(d)
                    if rt and rt.path not in seen:
                        found.append(rt)
                        seen.add(rt.path)
        compat = steam / "compatibilitytools.d"
        if compat.is_dir():
            for d in sorted(compat.iterdir(), key=lambda p: p.name.lower(), reverse=True):
                if not d.is_dir():
                    continue
                bin_ = _proton_binary(d)
                if bin_.exists() or (d / "version").exists() or (d / "compatibilitytool.vdf").exists():
                    rt = _make_proton(d)
                    if rt and rt.path not in seen:
                        found.append(rt)
                        seen.add(rt.path)
    return found


def list_wine_runtimes() -> list[Runtime]:
    found: list[Runtime] = []
    for name in ("wine64", "wine"):
        w = shutil.which(name)
        if w:
            p = Path(w)
            found.append(
                Runtime(
                    kind="wine",
                    binary=p,
                    name=f"System {name}",
                    path=str(p),
                    id=f"wine:{p}",
                )
            )
            break
    return found


def list_runtimes() -> list[Runtime]:
    return list_proton_runtimes() + list_wine_runtimes()


def find_proton(explicit: str = "") -> Runtime | None:
    if explicit:
        p = Path(explicit)
        if p.exists():
            root = p if p.is_dir() else p.parent
            return _make_proton(root, name=root.name) or Runtime(
                kind="proton",
                binary=_proton_binary(p),
                proton_root=root,
                name=root.name,
                path=str(root),
                id=f"proton:{root}",
            )
    protons = list_proton_runtimes()
    return protons[0] if protons else None


def find_wine(explicit: str = "") -> Runtime | None:
    if explicit:
        p = Path(explicit)
        if p.exists():
            return Runtime(
                kind="wine",
                binary=p,
                name=p.name,
                path=str(p),
                id=f"wine:{p}",
            )
    wines = list_wine_runtimes()
    return wines[0] if wines else None


def detect_runtime() -> Runtime | None:
    cfg = load_config()
    preferred = (cfg.get("preferred_runtime") or "auto").lower()
    default_id = cfg.get("default_runtime_id") or ""

    if default_id:
        for rt in list_runtimes():
            if rt.id == default_id or rt.path == default_id:
                return rt

    proton = find_proton(cfg.get("proton_path") or "")
    wine = find_wine(cfg.get("wine_path") or "")

    if preferred == "proton":
        return proton or wine
    if preferred == "wine":
        return wine or proton
    return proton or wine


def set_default_runtime(runtime_id: str) -> dict[str, str] | None:
    for rt in list_runtimes():
        if rt.id == runtime_id or rt.path == runtime_id:
            cfg = load_config()
            cfg["default_runtime_id"] = rt.id
            if rt.kind == "proton":
                cfg["proton_path"] = rt.path
            else:
                cfg["wine_path"] = rt.path
            save_config(cfg)
            return rt.as_dict()
    return None


def which_winetricks() -> Path | None:
    w = shutil.which("winetricks") or shutil.which("protontricks")
    return Path(w) if w else None


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
    """Download latest Proton-GE release into compatibilitytools.d (Linux only)."""
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
                # Safe extract: reject path traversal
                for member in tar.getmembers():
                    member_path = Path(dest_root) / member.name
                    if not str(member_path.resolve()).startswith(str(dest_root.resolve())):
                        return {"ok": False, "message": "Unsafe archive paths rejected.", "path": ""}
                tar.extractall(dest_root)
    except (urllib.error.URLError, OSError, tarfile.TarError, TimeoutError) as exc:
        return {"ok": False, "message": f"Install failed: {exc}", "path": ""}

    # Prefer folder matching tag
    installed = dest_root / tag
    if not installed.exists():
        candidates = [
            d
            for d in dest_root.iterdir()
            if d.is_dir() and ("GE-Proton" in d.name or "Proton" in d.name)
        ]
        installed = max(candidates, key=lambda p: p.stat().st_mtime) if candidates else dest_root

    cfg = load_config()
    cfg["proton_path"] = str(installed)
    cfg["default_runtime_id"] = f"proton:{installed}"
    save_config(cfg)
    return {
        "ok": True,
        "message": f"Installed {tag} to {installed}",
        "path": str(installed),
        "tag": tag,
    }
