"""Tests for version lookup logic. The Anthropic client is faked; no API calls."""

from types import SimpleNamespace

import pytest

from version_agent.checker import NOT_FOUND, compare, extract_version, find_latest_version


def reply(text, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)]
    )


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0.115.4", "0.115.4"),
        ("The latest stable version is v1.9.8.", "1.9.8"),
        ("3.13", "3.13"),
        ("NOT_FOUND", NOT_FOUND),
        ("", NOT_FOUND),
        ("no idea", NOT_FOUND),
    ],
)
def test_extract_version(text, expected):
    assert extract_version(text) == expected


@pytest.mark.parametrize(
    ("current", "latest", "expected"),
    [
        ("1.2.0", "1.2.0", "UP_TO_DATE"),
        ("1.3.0", "1.2.0", "UP_TO_DATE"),
        ("1.2.0", "1.10.0", "OUTDATED"),
        ("", "1.0.0", "NO_CURRENT_VERSION"),
        ("1.0.0", NOT_FOUND, "UNKNOWN"),
        ("latest", "1.0.0", "CHECK_MANUALLY"),
    ],
)
def test_compare(current, latest, expected):
    assert compare(current, latest) == expected


def test_find_latest_version_uses_url_in_prompt():
    client = FakeClient(reply("2.0.1"))
    assert find_latest_version(client, "terraform", "https://example.com") == "2.0.1"
    prompt = client.calls[0]["messages"][0]["content"]
    assert "terraform" in prompt and "https://example.com" in prompt


def test_find_latest_version_continues_after_pause_turn():
    client = FakeClient(reply("", stop_reason="pause_turn"), reply("1.5.0"))
    assert find_latest_version(client, "pkg") == "1.5.0"
    assert len(client.calls) == 2
    assert client.calls[1]["messages"][-1]["role"] == "assistant"
