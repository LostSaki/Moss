"""Optional OpenAI-compatible log advisor (Moss 0.3.0). Opt-in only."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from moss.store import load_config
from moss.suggest import Suggestion, SuggestContext, redact_for_ai


def _cfg_ai() -> dict[str, Any]:
    cfg = load_config()
    return {
        "enabled": bool(cfg.get("ai_suggestions_enabled")),
        "endpoint": str(cfg.get("ai_endpoint") or "").rstrip("/"),
        "api_key": str(cfg.get("ai_api_key") or ""),
        "model": str(cfg.get("ai_model") or "gpt-4o-mini"),
    }


def suggest_fixes_ai(ctx: SuggestContext) -> list[Suggestion]:
    conf = _cfg_ai()
    if not conf["enabled"] or not conf["endpoint"]:
        return []
    payload = {
        "model": conf["model"],
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You help diagnose Windows games running under Proton/Wine via Moss. "
                    "Reply with JSON only: {\"suggestions\":[{\"id\":\"...\",\"title\":\"...\","
                    "\"detail\":\"...\",\"action\":\"winetricks|report|change_exe|open_url\","
                    "\"verb\":\"\",\"url\":\"\"}]}. Max 4 suggestions. Be concise."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(redact_for_ai(ctx)),
            },
        ],
    }
    url = conf["endpoint"]
    if not url.endswith("/chat/completions"):
        url = f"{url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Moss-AI-Suggest",
    }
    if conf["api_key"]:
        headers["Authorization"] = f"Bearer {conf['api_key']}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return [
            Suggestion(
                id="ai-error",
                title="AI suggestion unavailable",
                detail="Could not reach the configured AI endpoint.",
                action="report",
                source="ai",
            )
        ]
    try:
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        # Strip markdown fences if present
        text = str(content).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        parsed = json.loads(text)
        rows = parsed.get("suggestions") if isinstance(parsed, dict) else parsed
        out: list[Suggestion] = []
        for item in rows or []:
            if not isinstance(item, dict):
                continue
            out.append(
                Suggestion(
                    id=str(item.get("id") or f"ai-{len(out)}"),
                    title=str(item.get("title") or "Suggestion"),
                    detail=str(item.get("detail") or ""),
                    action=str(item.get("action") or "report"),
                    verb=str(item.get("verb") or ""),
                    url=str(item.get("url") or ""),
                    source="ai",
                )
            )
        return out[:4]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return []
