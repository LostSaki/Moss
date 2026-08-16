from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import yaml

DLL_TO_VERB = {
    "vcruntime140.dll": "vcrun2019",
    "vcruntime140_1.dll": "vcrun2019",
    "msvcp140.dll": "vcrun2019",
    "msvcp140_1.dll": "vcrun2019",
    "d3dcompiler_47.dll": "d3dcompiler_47",
    "xaudio2_7.dll": "xact",
    "x3daudio1_7.dll": "xact",
    "d3dx9_43.dll": "d3dx9",
    "d3dx11_43.dll": "d3dcompiler_43",
}

IMPORT_DLL_RE = re.compile(
    r"import_dll.*?(?:Library )?(?P<dll>[A-Za-z0-9_\-\.]+\.dll)",
    re.IGNORECASE,
)


@dataclass
class RecipeMatch:
    recipe_id: str
    action: str
    verb: str | None = None
    message: str | None = None
    dll: str | None = None


def load_recipes(path: Path | None = None) -> list[dict]:
    if path is None:
        data = files("moss").joinpath("recipes.yaml").read_text(encoding="utf-8")
    else:
        data = Path(path).read_text(encoding="utf-8")
    raw = yaml.safe_load(data) or {}
    if isinstance(raw, dict):
        return raw.get("recipes") or []
    return raw


def match_log(log_text: str, recipes: list[dict] | None = None) -> RecipeMatch | None:
    recipes = recipes if recipes is not None else load_recipes()
    text = log_text
    for recipe in recipes:
        patterns = [p for p in (recipe.get("patterns") or []) if isinstance(p, str)]
        if not any(p in text for p in patterns):
            continue
        action = recipe.get("action", "report")
        if action == "map_dll":
            m = IMPORT_DLL_RE.search(text)
            dll = m.group("dll").lower() if m else None
            verb = DLL_TO_VERB.get(dll) if dll else None
            if verb:
                return RecipeMatch(
                    recipe_id=recipe.get("id", "import_dll"),
                    action="winetricks",
                    verb=verb,
                    dll=dll,
                )
            return RecipeMatch(
                recipe_id=recipe.get("id", "import_dll"),
                action="report",
                dll=dll,
                message=f"Unknown missing DLL: {dll or '(name not parsed)'}. Stopping auto-fix.",
            )
        return RecipeMatch(
            recipe_id=recipe.get("id", "unknown"),
            action=action,
            verb=recipe.get("verb"),
            message=recipe.get("message"),
        )
    return None
