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


def check_for_update(current: str | None = None) -> UpdateInfo:
    current = current or __version__
    data = _get(f"{GITHUB_API}/releases/latest")
    if data and data.get("tag_name"):
        tag = str(data["tag_name"])
        url = data.get("html_url") or RELEASES_URL
        if _newer(tag, current):
            return UpdateInfo(True, latest=tag, url=url, message=f"Update {tag} available")
        return UpdateInfo(False, latest=tag, url=url)
    return UpdateInfo(False, latest=current, url=REPO_URL)
