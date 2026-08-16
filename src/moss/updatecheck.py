from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from moss import __version__

GITHUB_API = "https://api.github.com/repos/LostSaki/Moss"
RELEASES_URL = "https://github.com/LostSaki/Moss/releases"
REPO_URL = "https://github.com/LostSaki/Moss"


@dataclass
class UpdateInfo:
    available: bool
    latest: str = ""
    url: str = RELEASES_URL
    message: str = ""
    current: str = ""
    ok: bool = True  # False when network/API failed


def _get(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": "Moss-UpdateCheck"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _newer(latest: str, current: str) -> bool:
    def parts(v: str) -> tuple[int, ...]:
        v = v.lstrip("vV")
        nums = []
        for chunk in v.replace("-", ".").split("."):
            if chunk.isdigit():
                nums.append(int(chunk))
        return tuple(nums or [0])

    return parts(latest) > parts(current)


def _fmt_ver(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return ""
    return v if v.lower().startswith("v") else f"v{v}"


def check_for_update(current: str | None = None) -> UpdateInfo:
    current = current or __version__
    cur_label = _fmt_ver(current)
    data = _get(f"{GITHUB_API}/releases/latest")
    if data is None:
        return UpdateInfo(
            available=False,
            latest="",
            current=current,
            url=RELEASES_URL,
            message="Couldn't reach GitHub · try again later",
            ok=False,
        )
    if data.get("tag_name"):
        tag = str(data["tag_name"])
        url = data.get("html_url") or RELEASES_URL
        if _newer(tag, current):
            return UpdateInfo(
                available=True,
                latest=tag,
                current=current,
                url=url,
                message=f"Update available · {_fmt_ver(tag)} (you have {cur_label})",
                ok=True,
            )
        return UpdateInfo(
            available=False,
            latest=tag,
            current=current,
            url=url,
            message=f"You're up to date · {cur_label}",
            ok=True,
        )
    return UpdateInfo(
        available=False,
        latest="",
        current=current,
        url=RELEASES_URL,
        message="Couldn't reach GitHub · try again later",
        ok=False,
    )
