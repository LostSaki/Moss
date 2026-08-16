from __future__ import annotations

import os
import subprocess
from pathlib import Path

from moss.paths import prefixes_dir
from moss.runtime import Runtime, detect_runtime
from moss.scan import slug_id


def prefix_for(game_id: str) -> Path:
    return prefixes_dir() / slug_id(game_id) / "pfx"


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
