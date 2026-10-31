"""Tests for the single-shot generation engine."""

from pathlib import Path

import pytest

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
    valid_suites = [
        "from testpilot_target import double\n"
        "def test_double():\n    assert double(3) == 6\n",
        "from testpilot_target import double as target\n"
        "def test_double():\n    assert target(3) == 6\n",
        "import testpilot_target\n"
        "def test_double():\n    assert testpilot_target.double(3) == 6\n",
        "import testpilot_target as module_0\n"
        "def test_double():\n    assert module_0.double(3) == 6\n",
    ]
    for suite in valid_suites:
        assert target_usage_issue(suite, "double") is None

    invalid_suites = [
        (
            "from testpilot_target import double\n"
            "def test_double():\n    assert 3 == 3\n",
            "no pytest test directly calls",
        ),
        (
            "from testpilot_target import double\n"
            "double = lambda value: value\n"
            "def test_double():\n    assert double(3) == 3\n",
            "shadows imported target binding",
        ),
        (
            "import testpilot_target as module_0\n"
            "module_0 = object()\n"
            "def test_double():\n    assert module_0.double(3) == 6\n",
            "shadows imported target binding",
        ),
        (
            "import testpilot_target as module_0\n"
            "module_0.double = lambda value: value\n"
            "def test_double():\n    assert module_0.double(3) == 3\n",
            "redefines target attribute",
        ),
        (
            "def double(value):\n    return value * 2\n"
            "def test_double():\n    assert double(3) == 6\n",
            "defines 'double'",
        ),
    ]
    for suite, expected_issue in invalid_suites:
        assert expected_issue in (target_usage_issue(suite, "double") or "")


def test_target_usage_validation_accepts_saved_pynguin_module_alias() -> None:
    fixture_path = (
        Path(__file__).parent / "fixtures" / "pynguin_module_alias.py"
    )

    assert target_usage_issue(
        fixture_path.read_text(encoding="utf-8"),
        "has_close_elements",
    ) is None


def test_target_usage_validation_allows_pytest_suites_with_noncalling_tests() -> None:
    suite = (
        "import testpilot_target as module_0\n"
        "def test_helper_only():\n    assert True\n"
        "def test_calls_target():\n    assert module_0.double(3) == 6\n"
    )

    assert target_usage_issue(suite, "double") is None


@pytest.mark.parametrize(
    "suite",
    [
        "from testpilot_target import double as target\n"
        "def test_double():\n    assert target(3) == 6\n",
        "import testpilot_target as module_0\n"
        "def test_double():\n    assert module_0.double(3) == 6\n",
    ],
)
def test_target_usage_validation_allows_alias_parameters_in_tests(
    suite: str,
) -> None:
    assert target_usage_issue(suite, "double") is None


def test_single_shot_engine_rejects_empty_completion() -> None:
    function = analyze_source("def f():\n    return None\n")[0]

    try:
        SingleShotEngine(FakeProvider("```python\n```")).generate(function, Path("f.py"))
    except ValueError as exc:
        assert "empty test suite" in str(exc)
    else:
        raise AssertionError("Expected an empty completion to be rejected")
