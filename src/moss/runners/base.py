from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Runner:
    """Discovered Wine/Proton runtime used for launch and prefix ops."""

    kind: str  # proton | wine
    binary: Path
    proton_root: Path | None = None
    name: str = ""
    path: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        root = self.proton_root or self.binary
        if not self.path:
            self.path = str(root)
        if not self.name:
            self.name = Path(self.path).name if self.path else self.kind
        if not self.id:
            self.id = f"{self.kind}:{self.path}"

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "path": self.path,
            "binary": str(self.binary),
        }

    def exists(self) -> bool:
        return self.binary.exists() or (self.proton_root is not None and Path(self.path).exists())


# Back-compat alias used across launch/prefix/components
Runtime = Runner


def runner_from_dict(data: dict[str, Any]) -> Runner:
    root = Path(str(data.get("path") or data.get("binary") or ""))
    binary = Path(str(data.get("binary") or root))
    kind = str(data.get("kind") or "wine")
    proton_root = root if kind == "proton" and root.is_dir() else None
    return Runner(
        kind=kind,
        binary=binary,
        proton_root=proton_root,
        name=str(data.get("name") or ""),
        path=str(data.get("path") or root),
        id=str(data.get("id") or ""),
    )
