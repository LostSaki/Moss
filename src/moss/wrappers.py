from __future__ import annotations

import os
import shutil
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from moss.store import Game


def which(name: str) -> str | None:
    return shutil.which(name)


@dataclass
class ToolStatus:
    gamescope: bool
    mangohud: bool
    gamemode: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "gamescope": self.gamescope,
            "mangohud": self.mangohud,
            "gamemode": self.gamemode,
        }


def detect_tools() -> ToolStatus:
    return ToolStatus(
        gamescope=which("gamescope") is not None,
        mangohud=which("mangohud") is not None or which("mangohudctl") is not None,
        gamemode=which("gamemoderun") is not None,
    )


def _parse_args(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def wrap_command(game: Game, base_cmd: list[str], env: dict[str, str]) -> tuple[list[str], dict[str, str], list[str]]:
    """Wrap launch argv with optional GameMode / Gamescope / MangoHud.

    Returns (cmd, env, warnings).
    """
    warnings: list[str] = []
    cmd = list(base_cmd)
    env = dict(env)
    tools = detect_tools()

    if getattr(game, "mangohud_enabled", False):
        if tools.mangohud:
            env["MANGOHUD"] = "1"
            # Prefer mangohud wrapper when available
            mh = which("mangohud")
            if mh:
                cmd = [mh, *cmd]
        else:
            warnings.append("MangoHud not found on PATH — skipped.")

    if getattr(game, "gamescope_enabled", False):
        gs = which("gamescope")
        if gs:
            extra = _parse_args(getattr(game, "gamescope_args", "") or "")
            cmd = [gs, *extra, "--", *cmd]
        else:
            warnings.append("Gamescope not found on PATH — skipped.")

    if getattr(game, "gamemode_enabled", False):
        gm = which("gamemoderun")
        if gm:
            cmd = [gm, *cmd]
        else:
            warnings.append("GameMode (gamemoderun) not found on PATH — skipped.")

    return cmd, env, warnings


def host_tools_summary() -> dict[str, Any]:
    tools = detect_tools()
    return {
        **tools.as_dict(),
        "platform": os.name,
        "isLinux": os.name == "posix" and Path("/").exists(),
    }
