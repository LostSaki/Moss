from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SKIP_NAME_RE = re.compile(
    r"(uninstall|unins\d+|redist|vcredist|directx|dxsetup|crashreporter|"
    r"unitycrashhandler|crashpad|helper|setup_info|dotnet|oalinst|"
    r"easyanticheat|eac_launcher|battleye)",
    re.IGNORECASE,
)

SKIP_DIR_RE = re.compile(
    r"(__redist|redist|_commonredist|directx|support|crashreporter|eac|battleye)",
    re.IGNORECASE,
)

SCORE_HINTS = (
    ("launcher", -8),
    ("start", 4),
    ("game", 3),
    ("win64", 2),
    ("x64", 2),
)


@dataclass
class FoundExe:
    path: Path
    score: int


def should_skip_exe(path: Path) -> bool:
    if path.suffix.lower() != ".exe":
        return True
    if SKIP_NAME_RE.search(path.stem):
        return True
    for part in path.parts:
        if SKIP_DIR_RE.fullmatch(part) or SKIP_DIR_RE.search(part):
            return True
    return False


def score_exe(path: Path, folder_name: str = "") -> int:
    name = path.stem.lower()
    score = 10
    if folder_name and folder_name.lower() in name:
        score += 12
    if name == folder_name.lower():
        score += 8
    for hint, delta in SCORE_HINTS:
        if hint in name:
            score += delta
    # Prefer files closer to the game root
    score -= len(path.parts) * 1
    return score


def scan_folder(root: Path) -> list[FoundExe]:
    root = Path(root)
    if not root.is_dir():
        return []
    found: list[FoundExe] = []
    for path in root.rglob("*.exe"):
        if not path.is_file() or should_skip_exe(path):
            continue
        found.append(FoundExe(path=path, score=score_exe(path, root.name)))
    found.sort(key=lambda f: f.score, reverse=True)
    return found


def pick_main_exe(root: Path) -> Path | None:
    found = scan_folder(root)
    return found[0].path if found else None


def slug_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "game"


def display_name_from_path(exe: Path) -> str:
    parent = exe.parent.name
    if parent.lower() in {"bin", "binaries", "win64", "win32", "x64", "x86"}:
        parent = exe.parent.parent.name if exe.parent.parent else exe.stem
    pretty = re.sub(r"[_\-]+", " ", parent).strip()
    return pretty.title() if pretty else exe.stem
