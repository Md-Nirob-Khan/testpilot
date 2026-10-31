"""Tests for the single-shot generation engine."""

from pathlib import Path

from testpilot.analyzer import analyze_source
from testpilot.engines import SingleShotEngine
from testpilot.engines.llm_engine import target_usage_issue
from testpilot.llm import LLMResponse


class FakeProvider:
    """Return a known completion and retain its prompts for assertions."""

    def __init__(self, content: str | list[str]) -> None:
        self.contents = iter([content] if isinstance(content, str) else content)
        self.prompts: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.prompts.append((system_prompt, user_prompt))
        return LLMResponse(next(self.contents), 4, 6, 0.012)


def test_single_shot_engine_strips_outer_fence_and_records_metrics() -> None:
    function = analyze_source("def double(value: int) -> int:\n    return value * 2\n")[0]
    provider = FakeProvider(
        "```python\n"
        "from testpilot_target import double\n\n"
        "def test_double():\n"
        "    assert double(3) == 6\n"
        "```"
    )

    suite = SingleShotEngine(provider).generate(function, Path("sample.py"))

    assert suite.test_code == (
        "from testpilot_target import double\n\n"
        "def test_double():\n"
        "    assert double(3) == 6"
    )
    assert suite.engine_name == "single-shot-llm"
    assert suite.llm_tokens_used == 10
    assert suite.estimated_cost_usd == 0.012
    assert suite.rounds == 1
    assert suite.wall_clock_seconds >= 0
    assert "testpilot_target" in provider.prompts[0][1]
    assert "from testpilot_target import double" in provider.prompts[0][1]
    assert (
        "Import the function from testpilot_target and do not copy or redefine it."
        in provider.prompts[0][1]
    )


def test_single_shot_makes_exactly_one_attempt_for_invalid_target_usage() -> None:
    function = analyze_source("def double(value: int) -> int:\n    return value * 2\n")[0]
    invalid = "def double(value):\n    return value * 2\n\ndef test_double():\n    assert double(3) == 6"
    provider = FakeProvider([invalid])

    suite = SingleShotEngine(provider).generate(function, Path("sample.py"))

    assert suite.test_code == invalid
    assert suite.rounds == 1
    assert suite.llm_tokens_used == 10
    assert suite.estimated_cost_usd == 0.012
    assert len(provider.prompts) == 1
    assert target_usage_issue(suite.test_code, "double") is not None


def test_target_usage_validation_requires_direct_calls_to_the_imported_target() -> None:
    aliased_import = (
        "from testpilot_target import double as target\n\n"
        "def test_double():\n"
        "    assert target(3) == 6\n"
    )
    imported_but_unused = (
        "from testpilot_target import double\n\n"
        "def test_double():\n"
        "    assert 3 == 3\n"
    )
    shadowed_import = (
        "from testpilot_target import double\n"
        "double = lambda value: value\n\n"
        "def test_double():\n"
        "    assert double(3) == 3\n"
    )

    assert target_usage_issue(aliased_import, "double") is None
    assert "does not directly call" in (
        target_usage_issue(imported_but_unused, "double") or ""
    )
    assert "shadows imported target binding" in (
        target_usage_issue(shadowed_import, "double") or ""
    )


def test_single_shot_engine_rejects_empty_completion() -> None:
    function = analyze_source("def f():\n    return None\n")[0]

    try:
        SingleShotEngine(FakeProvider("```python\n```")).generate(function, Path("f.py"))
    except ValueError as exc:
        assert "empty test suite" in str(exc)
    else:
        raise AssertionError("Expected an empty completion to be rejected")
