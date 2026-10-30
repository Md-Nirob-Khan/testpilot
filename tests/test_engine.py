"""Tests for the single-shot generation engine."""

from pathlib import Path

from testpilot.analyzer import analyze_source
from testpilot.engines import SingleShotEngine
from testpilot.llm import LLMResponse


class FakeProvider:
    """Return a known completion and retain its prompts for assertions."""

    def __init__(self, content: str) -> None:
        self.content = content
        self.prompts: tuple[str, str] | None = None

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.prompts = (system_prompt, user_prompt)
        return LLMResponse(self.content, 4, 6, 0.012)


def test_single_shot_engine_strips_outer_fence_and_records_metrics() -> None:
    function = analyze_source("def double(value: int) -> int:\n    return value * 2\n")[0]
    provider = FakeProvider("```python\nimport pytest\n\ndef test_double():\n    assert True\n```")

    suite = SingleShotEngine(provider).generate(function, Path("sample.py"))

    assert suite.test_code == "import pytest\n\ndef test_double():\n    assert True"
    assert suite.engine_name == "single-shot-llm"
    assert suite.llm_tokens_used == 10
    assert suite.estimated_cost_usd == 0.012
    assert suite.rounds == 1
    assert suite.wall_clock_seconds >= 0
    assert provider.prompts is not None
    assert "testpilot_target" in provider.prompts[1]
    assert "from testpilot_target import double" in provider.prompts[1]
    assert "def double" in provider.prompts[1]


def test_single_shot_engine_rejects_empty_completion() -> None:
    function = analyze_source("def f():\n    return None\n")[0]

    try:
        SingleShotEngine(FakeProvider("```python\n```")).generate(function, Path("f.py"))
    except ValueError as exc:
        assert "empty test suite" in str(exc)
    else:
        raise AssertionError("Expected an empty completion to be rejected")
