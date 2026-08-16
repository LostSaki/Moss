"""Runner discovery package (Wine / Proton)."""

from moss.runners.base import Runner, Runtime, runner_from_dict
from moss.runners.manager import (
    detect_default,
    get_runner,
    list_runners,
    resolve_for_game,
    set_default_runner,
)

__all__ = [
    "Runner",
    "Runtime",
    "runner_from_dict",
    "list_runners",
    "get_runner",
    "detect_default",
    "resolve_for_game",
    "set_default_runner",
]
