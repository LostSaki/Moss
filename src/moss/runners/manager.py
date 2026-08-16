from __future__ import annotations

from typing import TYPE_CHECKING

from moss.runners.base import Runner
from moss.runners.proton import (
    discover_proton,
    find_proton,
    install_proton_ge,
    proton_ge_status,
)
from moss.runners.wine import discover_wine, find_wine
from moss.store import load_config, save_config

if TYPE_CHECKING:
    from moss.store import Game


def list_runners() -> list[Runner]:
    cfg = load_config()
    protons = discover_proton(cfg.get("proton_path") or "")
    wines = discover_wine(cfg.get("wine_path") or "")
    # Prefer discovered list without duplicating explicit path entries
    seen: set[str] = set()
    out: list[Runner] = []
    for rt in protons + wines:
        if rt.id in seen or rt.path in seen:
            continue
        out.append(rt)
        seen.add(rt.id)
        seen.add(rt.path)
    return out


def get_runner(runner_id: str) -> Runner | None:
    if not runner_id:
        return None
    for rt in list_runners():
        if rt.id == runner_id or rt.path == runner_id:
            return rt
    # Allow unresolved explicit path ids
    if runner_id.startswith("proton:"):
        return find_proton(runner_id.split(":", 1)[1])
    if runner_id.startswith("wine:"):
        return find_wine(runner_id.split(":", 1)[1])
    return None


def detect_default() -> Runner | None:
    cfg = load_config()
    preferred = (cfg.get("preferred_runtime") or "auto").lower()
    default_id = cfg.get("default_runtime_id") or ""

    if default_id:
        rt = get_runner(default_id)
        if rt:
            return rt

    proton = find_proton(cfg.get("proton_path") or "")
    wine = find_wine(cfg.get("wine_path") or "")
    if preferred == "proton":
        return proton or wine
    if preferred == "wine":
        return wine or proton
    return proton or wine


def resolve_for_game(game: Game | None = None) -> Runner | None:
    """Per-game runner_id wins; otherwise config default / auto-detect."""
    if game is not None:
        rid = getattr(game, "runner_id", "") or ""
        if rid:
            rt = get_runner(rid)
            if rt:
                return rt
    return detect_default()


def set_default_runner(runner_id: str) -> dict[str, str] | None:
    rt = get_runner(runner_id)
    if not rt:
        return None
    cfg = load_config()
    cfg["default_runtime_id"] = rt.id
    if rt.kind == "proton":
        cfg["proton_path"] = rt.path
    else:
        cfg["wine_path"] = rt.path
    save_config(cfg)
    return rt.as_dict()


def after_ge_install(result: dict) -> dict:
    """Persist default when GE install succeeds."""
    if not result.get("ok"):
        return result
    path = result.get("path") or ""
    rid = result.get("runner_id") or (f"proton:{path}" if path else "")
    if rid:
        set_default_runner(rid)
    return result


__all__ = [
    "list_runners",
    "get_runner",
    "detect_default",
    "resolve_for_game",
    "set_default_runner",
    "install_proton_ge",
    "proton_ge_status",
    "after_ge_install",
]
