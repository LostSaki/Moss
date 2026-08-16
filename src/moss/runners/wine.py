from __future__ import annotations

import os
import shutil
from pathlib import Path

from moss.runners.base import Runner


def discover_wine(explicit: str = "") -> list[Runner]:
    found: list[Runner] = []
    seen: set[str] = set()

    if explicit:
        p = Path(explicit)
        if p.exists():
            rt = Runner(kind="wine", binary=p, name=p.name, path=str(p))
            found.append(rt)
            seen.add(rt.path)

    for name in ("wine64", "wine"):
        w = shutil.which(name)
        if not w:
            continue
        p = Path(w)
        if str(p) in seen:
            continue
        found.append(Runner(kind="wine", binary=p, name=f"System {name}", path=str(p)))
        seen.add(str(p))
        break
    return found


def find_wine(explicit: str = "") -> Runner | None:
    items = discover_wine(explicit)
    return items[0] if items else None
