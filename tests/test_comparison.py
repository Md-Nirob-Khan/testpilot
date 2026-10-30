"""Tests for engine comparison and honest evaluator reporting."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from testpilot.analyzer import analyze_source
from testpilot.comparison import compare_functions
from testpilot.engines.base import GeneratedSuite


class _FakeEngine:
    def generate(self, function_info, source_path):
        return GeneratedSuite(
            test_code=f"def test_{function_info.name}():\n    assert True\n",
            engine_name="fake",
            wall_clock_seconds=0.1,
            llm_tokens_used=0,
            estimated_cost_usd=0,
        )


class _FakeWrongTestDetector:
    def __init__(self, events):
        self.events = events

    def evaluate(self, test_code, source_path, is_benchmark):
        self.events.append("wrong-test")
        return SimpleNamespace(status="passed", failing_tests=0)


class _FakeCoverageEvaluator:
    def __init__(self, events):
        self.events = events

    def evaluate(self, test_code, source_path):
        self.events.append("coverage")
        return SimpleNamespace(line_percent=75.0, branch_percent=50.0)


class _FakeMutationEvaluator:
    def __init__(self, events):
        self.events = events

    def evaluate(self, test_code, source_path):
        self.events.append("mutation")
        return SimpleNamespace(mutation_score=0.8)


def test_comparison_measures_suite_and_runs_correctness_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.comparison as comparison

    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n")
    function = analyze_source(
        "def add(left, right):\n    return left + right\n"
    )[0]
    events: list[str] = []
    monkeypatch.setattr(
        comparison,
        "WrongTestDetector",
        lambda: _FakeWrongTestDetector(events),
    )
    monkeypatch.setattr(
        comparison,
        "CoverageEvaluator",
        lambda: _FakeCoverageEvaluator(events),
    )
    monkeypatch.setattr(
        comparison,
        "MutationEvaluator",
        lambda: _FakeMutationEvaluator(events),
    )

    results = compare_functions(
        source_path,
        [function],
        ["Pynguin"],
        engine_factories={"Pynguin": _FakeEngine},
    )

    assert events == ["wrong-test", "coverage", "mutation"]
    assert results[0].engine_name == "pynguin"
    assert results[0].line_percent == 75
    assert results[0].branch_percent == 50
    assert results[0].mutation_score == 0.8
    assert results[0].wrong_test_status == "passed"
    assert results[0].test_code is not None


def test_comparison_does_not_score_mutation_for_failing_suite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.comparison as comparison

    source_path = tmp_path / "subject.py"
    source_path.write_text("def value():\n    return 1\n")
    function = analyze_source("def value():\n    return 1\n")[0]
    events: list[str] = []
    monkeypatch.setattr(
        comparison,
        "WrongTestDetector",
        lambda: SimpleNamespace(
            evaluate=lambda *args, **kwargs: SimpleNamespace(
                status="needs_human_review",
                failing_tests=1,
            )
        ),
    )
    monkeypatch.setattr(
        comparison,
        "CoverageEvaluator",
        lambda: _FakeCoverageEvaluator(events),
    )
    monkeypatch.setattr(
        comparison,
        "MutationEvaluator",
        lambda: _FakeMutationEvaluator(events),
    )

    result = compare_functions(
        source_path,
        [function],
        ["Pynguin"],
        engine_factories={"Pynguin": _FakeEngine},
    )[0]

    assert events == ["coverage"]
    assert result.wrong_test_count == 1
    assert result.wrong_test_status == "needs_human_review"
    assert result.mutation_score is None


def test_comparison_rejects_empty_or_unknown_selections(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def value():\n    return 1\n")
    function = analyze_source("def value():\n    return 1\n")[0]

    with pytest.raises(ValueError, match="Select at least one function"):
        compare_functions(source_path, [], ["Pynguin"])
    with pytest.raises(ValueError, match="Select at least one engine"):
        compare_functions(source_path, [function], [])
    with pytest.raises(ValueError, match="Unknown engines"):
        compare_functions(source_path, [function], ["Unknown"])
