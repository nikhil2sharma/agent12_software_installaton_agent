"""Version lookup and comparison."""

import logging
import re
from typing import Any

import anthropic
from packaging.version import InvalidVersion, Version

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-5-5"
NOT_FOUND = "NOT_FOUND"
MAX_CONTINUATIONS = 3
WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 3}

_VERSION_RE = re.compile(r"\bv?(\d+(?:\.\d+){0,3}(?:[-.]?(?:a|b|rc)\d+)?)\b")


def build_prompt(name: str, url: str = "") -> str:
    prompt = f"What is the latest stable version of '{name}'?"
    if url:
        prompt += f" Check this source first: {url}"
    return (
        prompt + " Reply with ONLY the version number, like 1.2.3. If not found, reply NOT_FOUND."
    )


def extract_version(text: str) -> str:
    """Pull the last version-looking token out of the model's reply."""
    if not text or NOT_FOUND in text:
        return NOT_FOUND
    matches = _VERSION_RE.findall(text)
    return matches[-1] if matches else NOT_FOUND


def find_latest_version(client: Any, name: str, url: str = "", model: str = DEFAULT_MODEL) -> str:
    """Ask Claude (with web search) for the latest stable version of a package."""
    messages: list[dict] = [{"role": "user", "content": build_prompt(name, url)}]
    try:
        for _ in range(MAX_CONTINUATIONS):
            resp = client.messages.create(
                model=model, max_tokens=1024, messages=messages, tools=[WEB_SEARCH_TOOL]
            )
            # Long server-side tool runs come back as pause_turn; send them back to continue.
            if resp.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": resp.content})
    except anthropic.APIError as exc:
        log.warning("Lookup failed for %s: %s", name, exc)
        return NOT_FOUND

    text = "".join(b.text for b in resp.content if b.type == "text")
    return extract_version(text)


def compare(current: str, latest: str) -> str:
    """Return UP_TO_DATE, OUTDATED, NO_CURRENT_VERSION, UNKNOWN or CHECK_MANUALLY."""
    if latest == NOT_FOUND:
        return "UNKNOWN"
    if not current:
        return "NO_CURRENT_VERSION"
    try:
        return "UP_TO_DATE" if Version(current) >= Version(latest) else "OUTDATED"
    except InvalidVersion:
        return "CHECK_MANUALLY"
