"""An empty Perplexity completion must raise, never return "".

No network: `requests.post` is stubbed with recorded response shapes.

Why this is a test and not a comment. `max_tokens` on a reasoning model is the
whole allowance, and the reasoning is spent first and is not itemized in
`completion_tokens`, so a budget the model can exhaust comes back with
`completion_tokens: 0`, empty content, and `finish_reason: "stop"` - a success by
every field a caller checks. Measured on sonar-reasoning-pro with a ~4k-token
prompt: 3500 through 5000 all returned nothing this way.

Every caller writes `result["text"]` into a vault note, so returning "" saves an
empty note under a real title and skips the fallback each call site already has.
That is worse than a visible failure, which is what the guard makes it.
"""

from __future__ import annotations

import os

import pytest

# Must run before the import below. `config.py` resolves OBSIDIAN_VAULT_PATH at
# import time and raises SystemExit when it is unset, and importing perplexity
# reaches it through usage.py. On a machine with no vault - which is every CI
# runner - that SystemExit escapes during collection and takes down the whole
# suite, not just this file: pytest reports INTERNALERROR and runs zero tests.
# setdefault so a real local vault is never overridden. Nothing here touches the
# filesystem; requests.post is stubbed in every test.
os.environ.setdefault("OBSIDIAN_VAULT_PATH", "/nonexistent/vault-for-tests")

from scripts.research.lib import perplexity  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = "stub"

    def json(self) -> dict:
        return self._payload


def _payload(content: str, *, completion_tokens: int, finish_reason: str = "stop") -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content},
                     "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 3994, "completion_tokens": completion_tokens,
                  "total_tokens": 3994 + completion_tokens},
    }


@pytest.fixture(autouse=True)
def _no_key_lookup(monkeypatch):
    monkeypatch.setattr(perplexity, "PERPLEXITY_API_KEY", lambda: "test-key")


def _stub(monkeypatch, payload: dict) -> list[int]:
    """Returns a mutable call counter so a test can assert there was no retry."""
    calls: list[int] = []

    def fake_post(*_a, **_kw):
        calls.append(1)
        return _FakeResponse(payload)

    monkeypatch.setattr(perplexity.requests, "post", fake_post)
    return calls


def test_empty_completion_raises_instead_of_returning_blank_text(monkeypatch):
    """The exact shape measured at max_tokens=3500: stop, 0 tokens, no content."""
    calls = _stub(monkeypatch, _payload("", completion_tokens=0))

    with pytest.raises(RuntimeError) as excinfo:
        perplexity.call("synthesize this", model="sonar-reasoning-pro", max_tokens=3500)

    message = str(excinfo.value)
    # The message has to name the budget, or the next person reads "empty
    # completion" as a provider outage and retries into the same wall.
    assert "max_tokens=3500" in message
    assert "empty completion" in message
    # No retry: when the budget is the cause it is deterministic, and retrying
    # bills the input again for the same nothing.
    assert len(calls) == 1


def test_whitespace_only_completion_also_raises(monkeypatch):
    """`.strip()` runs before the check, so blank-but-not-empty must not slip past."""
    _stub(monkeypatch, _payload("\n\n   \n", completion_tokens=4))

    with pytest.raises(RuntimeError):
        perplexity.call("synthesize this", model="sonar-reasoning-pro", max_tokens=3500)


def test_reasoning_only_completion_raises(monkeypatch):
    """An unclosed <think> is stripped to nothing by the existing rule above the
    guard. Before the guard that produced "" with no error at all."""
    _stub(monkeypatch, _payload("<think>weighing the sources", completion_tokens=500,
                                finish_reason="length"))

    with pytest.raises(RuntimeError):
        perplexity.call("synthesize this", model="sonar-reasoning-pro", max_tokens=3500)


def test_real_answer_still_returns_normally(monkeypatch):
    """The guard must not fire on a short-but-genuine answer."""
    _stub(monkeypatch, _payload("## What's New\n- a fact (2026-08, example.com)",
                                completion_tokens=18))

    result = perplexity.call("synthesize this", model="sonar-reasoning-pro", max_tokens=16000)

    assert result["text"].startswith("## What's New")
    assert result["model"] == "sonar-reasoning-pro"


def test_think_block_is_still_stripped_from_a_real_answer(monkeypatch):
    """Guard added below the existing strip, so closed reasoning still comes off."""
    _stub(monkeypatch, _payload("<think>deliberating</think>\n## Synthesis\n- point",
                                completion_tokens=40))

    result = perplexity.call("synthesize this", model="sonar-reasoning-pro", max_tokens=16000)

    assert "<think>" not in result["text"]
    assert result["text"].startswith("## Synthesis")
