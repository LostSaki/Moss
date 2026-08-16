from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from moss.store import load_config


@dataclass
class Runtime:
    kind: str  # proton | wine
    binary: Path
    proton_root: Path | None = None


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


def find_proton(explicit: str = "") -> Runtime | None:
    if explicit:
        p = Path(explicit)
        if p.exists():
            return Runtime(kind="proton", binary=_proton_binary(p), proton_root=p if p.is_dir() else p.parent)
    for steam in _steam_roots():
        common = steam / "steamapps" / "common"
        if common.is_dir():
            protons = sorted(
                [d for d in common.iterdir() if d.is_dir() and d.name.startswith("Proton")],
                key=lambda d: d.name,
                reverse=True,
            )
            for d in protons:
                bin_ = _proton_binary(d)
                if bin_.exists():
                    return Runtime(kind="proton", binary=bin_, proton_root=d)
        compat = steam / "compatibilitytools.d"
        if compat.is_dir():
            for d in sorted(compat.iterdir(), reverse=True):
                bin_ = _proton_binary(d)
                if d.is_dir() and bin_.exists():
                    return Runtime(kind="proton", binary=bin_, proton_root=d)
    return None


def _proton_binary(root: Path) -> Path:
    if root.is_file():
        return root
    for name in ("proton", "proton.sh"):
        cand = root / name
        if cand.exists():
            return cand
    return root / "proton"


def find_wine(explicit: str = "") -> Runtime | None:
    if explicit:
        p = Path(explicit)
        if p.exists():
            return Runtime(kind="wine", binary=p)
    wine = shutil.which("wine") or shutil.which("wine64")
    if wine:
        return Runtime(kind="wine", binary=Path(wine))
    return None


def detect_runtime() -> Runtime | None:
    cfg = load_config()
    return find_proton(cfg.get("proton_path") or "") or find_wine(cfg.get("wine_path") or "")


def which_winetricks() -> Path | None:
    w = shutil.which("winetricks") or shutil.which("protontricks")
    return Path(w) if w else None
