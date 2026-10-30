"""Tests for engine comparison and honest evaluator reporting."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from testpilot.analyzer import analyze_source
from testpilot.comparison import compare_functions
from testpilot.engines.base import GeneratedSuite
from testpilot.evaluator import MutationResult
from testpilot.sandbox import SandboxResult, TestOutcome


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
        return SimpleNamespace(
            status="passed",
            failing_tests=0,
            sandbox_result=SandboxResult(
                tests_run=1,
                passed=1,
                failed=0,
                errors=0,
                skipped=0,
                returncode=0,
                timed_out=False,
                wall_clock_seconds=0.1,
                stdout="",
                stderr="",
                test_outcomes=(TestOutcome("test_generated::test_add", "passed"),),
            ),
        )


class _FakeCoverageEvaluator:
    def __init__(self, events):
        self.events = events

    def evaluate(self, test_code, source_path, deselected_test_ids=()):
        self.events.append("coverage")
        return SimpleNamespace(line_percent=75.0, branch_percent=50.0)


class _FakeMutationEvaluator:
    def __init__(self, events):
        self.events = events

    def evaluate(self, test_code, source_path, deselected_test_ids=()):
        self.events.append("mutation")
        return MutationResult(
            total_mutants=1,
            killed_mutants=1,
            survived_mutants=0,
            timeout_mutants=0,
            mutation_score=1.0,
            surviving_mutant_names=(),
            wall_clock_seconds=0.1,
            stdout="",
            stderr="",
            killed_mutant_names=("mutant_1",),
        )


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

    assert events == [
        "wrong-test",
        "coverage",
        "mutation",
        "wrong-test",
        "mutation",
        "wrong-test",
        "mutation",
        "coverage",
    ]
    assert results[0].engine_name == "pynguin"
    assert results[0].line_percent == 75
    assert results[0].branch_percent == 50
    assert results[0].mutation_score == 1
    assert results[0].wrong_test_status == "passed"
    assert results[0].test_code is not None
    assert results[1].engine_name == "best-of-merge"
    assert results[1].status == "completed"
    assert results[1].merge_selected_test_names


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
                sandbox_result=SandboxResult(
                    tests_run=1,
                    passed=0,
                    failed=1,
                    errors=0,
                    skipped=0,
                    returncode=1,
                    timed_out=False,
                    wall_clock_seconds=0.1,
                    stdout="",
                    stderr="",
                    test_outcomes=(
                        TestOutcome("test_generated::test_add", "failed", "assertion_failure"),
                    ),
                ),
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

    assert events == []
    assert result.wrong_test_count == 1
    assert result.wrong_test_status == "needs_human_review"
    assert result.no_scorable_tests
    assert result.mutation_score == 0.0
    assert result.line_percent == 0.0
    assert result.branch_percent == 0.0


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
