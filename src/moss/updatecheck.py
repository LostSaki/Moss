from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from moss import __version__

GITHUB_API = "https://api.github.com/repos/LostSaki/Moss"
RELEASES_URL = "https://github.com/LostSaki/Moss/releases"
REPO_URL = "https://github.com/LostSaki/Moss"

_DEFAULT_HEADERS = {
    "User-Agent": "Moss-UpdateCheck",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


@dataclass
class UpdateInfo:
    available: bool
    latest: str = ""
    url: str = RELEASES_URL
    message: str = ""
    current: str = ""
    ok: bool = True  # False when network/API failed
    detail: str = ""  # machine-ish reason for debugging


def _ssl_context() -> ssl.SSLContext:
    """Prefer certifi CA bundle (helps frozen AppImage / portable builds)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _request_json(url: str, *, timeout: float = 12) -> tuple[Any | None, str]:
    """Return (parsed_json_or_None, error_detail)."""
    req = urllib.request.Request(url, headers=dict(_DEFAULT_HEADERS))
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw), ""
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        # 404 on /releases/latest is common when only prereleases exist
        return None, f"HTTP {exc.code}" + (f": {body}" if body else "")
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None) or exc
        return None, f"network: {reason}"
    except TimeoutError:
        return None, "timeout"
    except ssl.SSLError as exc:
        return None, f"ssl: {exc}"
    except (json.JSONDecodeError, OSError) as exc:
        return None, str(exc)


def _get(url: str) -> dict | None:
    data, _err = _request_json(url)
    return data if isinstance(data, dict) else None


def _get_list(url: str) -> list | None:
    data, _err = _request_json(url)
    return data if isinstance(data, list) else None


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


def _pick_stable_release() -> tuple[dict | None, str]:
    """Latest non-prerelease; fall back to list filter if /latest 404s."""
    data, err = _request_json(f"{GITHUB_API}/releases/latest")
    if isinstance(data, dict) and data.get("tag_name"):
        return data, ""
    # Fallback: scan recent releases for first non-prerelease, non-draft
    rows, list_err = _request_json(f"{GITHUB_API}/releases?per_page=20")
    if not isinstance(rows, list):
        return None, err or list_err or "Couldn't reach GitHub"
    for rel in rows:
        if not isinstance(rel, dict):
            continue
        if rel.get("draft"):
            continue
        if rel.get("prerelease"):
            continue
        if rel.get("tag_name"):
            return rel, ""
    # Only prereleases published — not an error; caller may use beta channel
    return None, "no_stable_release"


def _pick_beta_release() -> tuple[dict | None, str]:
    rows, err = _request_json(f"{GITHUB_API}/releases?per_page=15")
    if not isinstance(rows, list):
        return None, err or "Couldn't reach GitHub"
    for rel in rows:
        if not isinstance(rel, dict) or rel.get("draft"):
            continue
        if rel.get("tag_name"):
            return rel, ""
    return None, "no_releases"


def check_for_update(current: str | None = None, channel: str = "stable") -> UpdateInfo:
    """Stable = latest non-prerelease; beta = newest including prereleases."""
    current = current or __version__
    cur_label = _fmt_ver(current)
    channel = (channel or "stable").lower()

    if channel == "beta":
        rel, err = _pick_beta_release()
    else:
        rel, err = _pick_stable_release()

    if rel is None:
        if err == "no_stable_release":
            return UpdateInfo(
                available=False,
                current=current,
                url=RELEASES_URL,
                message=f"No stable release yet · you have {cur_label} · try Beta channel",
                ok=True,
                detail=err,
            )
        if err == "no_releases":
            return UpdateInfo(
                available=False,
                current=current,
                url=RELEASES_URL,
                message=f"You're up to date · {cur_label}",
                ok=True,
                detail=err,
            )
        hint = err or "unknown error"
        return UpdateInfo(
            available=False,
            latest="",
            current=current,
            url=RELEASES_URL,
            message=f"Couldn't reach GitHub · {hint}",
            ok=False,
            detail=hint,
        )

    tag = str(rel.get("tag_name") or "")
    url = str(rel.get("html_url") or RELEASES_URL)
    if not tag:
        return UpdateInfo(
            available=False,
            current=current,
            url=RELEASES_URL,
            message="Couldn't reach GitHub · empty release",
            ok=False,
            detail="empty_tag",
        )

    pre = bool(rel.get("prerelease"))
    if _newer(tag, current):
        ch = " (pre-release)" if pre else ""
        return UpdateInfo(
            available=True,
            latest=tag,
            current=current,
            url=url,
            message=f"Update available · {_fmt_ver(tag)}{ch} (you have {cur_label})",
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
