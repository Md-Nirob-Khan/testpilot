"""Known-answer and boundary tests for the evaluator."""

from pathlib import Path

import pytest

from testpilot.evaluator import (
    CoverageEvaluator,
    MutationEvaluator,
    WrongTestDetector,
)
from testpilot.evaluator.mutation import _subprocess_diagnostics
import subprocess


KNOWN_SOURCE = """\
def classify(value):
    if value > 0:
        return "positive"
    return "non-positive"
"""

KNOWN_COMPLETE_TESTS = """\
from testpilot_target import classify

def test_positive():
    assert classify(1) == "positive"

def test_non_positive():
    assert classify(0) == "non-positive"
"""


def _source_file(tmp_path: Path, source: str = KNOWN_SOURCE) -> Path:
    source_path = tmp_path / "subject.py"
    source_path.write_text(source, encoding="utf-8")
    return source_path


def test_coverage_known_answer_measures_all_lines_and_branches(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)

    result = CoverageEvaluator().evaluate(KNOWN_COMPLETE_TESTS, source_path)

    assert result.tests_run == 2
    assert result.passed == 2
    assert result.failed == result.errors == 0
    assert result.line_covered == result.line_total
    assert result.line_percent == 100
    assert result.branch_covered == result.branch_total == 2
    assert result.branch_percent == 100
    assert result.uncovered_lines == ()
    assert result.uncovered_branches == ()


def test_coverage_known_answer_reports_missing_line_and_branch(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)
    test_code = (
        "from testpilot_target import classify\n\n"
        "def test_positive():\n"
        "    assert classify(1) == 'positive'\n"
    )

    result = CoverageEvaluator().evaluate(test_code, source_path)

    assert result.line_percent == 75
    assert result.branch_percent == 50
    assert result.uncovered_lines == (4,)
    assert result.uncovered_branches == ((2, 4),)


def test_coverage_deselects_failing_test_and_measures_passing_case(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path)
    tests = (
        "from testpilot_target import classify\n\n"
        "def test_wrong():\n"
        "    assert classify(1) == 'negative'\n\n"
        "def test_right():\n"
        "    assert classify(1) == 'positive'\n"
    )

    result = CoverageEvaluator().evaluate(
        tests,
        source_path,
        ("tests/test_generated.py::test_wrong",),
    )

    assert result.tests_run == 1
    assert result.passed == 1
    assert result.failed == result.errors == 0


def test_coverage_rejects_non_finite_timeout() -> None:
    with pytest.raises(ValueError, match="finite positive"):
        CoverageEvaluator(float("inf"))


def test_coverage_requires_source_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        CoverageEvaluator().evaluate("def test_empty(): pass", tmp_path / "missing.py")


def test_wrong_test_detector_separates_benchmark_and_user_failures(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path)
    wrong_test = (
        "from testpilot_target import classify\n\n"
        "def test_wrong_expectation():\n"
        "    assert classify(1) == 'negative'\n"
    )
    detector = WrongTestDetector()

    benchmark_result = detector.evaluate(wrong_test, source_path, is_benchmark=True)
    user_result = detector.evaluate(wrong_test, source_path, is_benchmark=False)

    assert benchmark_result.status == "wrong_test"
    assert benchmark_result.failing_tests == 1
    assert user_result.status == "needs_human_review"
    assert user_result.failing_tests == 1


def test_wrong_test_detector_passes_correct_tests(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)

    result = WrongTestDetector().evaluate(
        KNOWN_COMPLETE_TESTS,
        source_path,
        is_benchmark=True,
    )

    assert result.status == "passed"
    assert result.failing_tests == 0


def test_wrong_test_detector_does_not_pass_collection_errors(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path)

    result = WrongTestDetector().evaluate(
        "def test_invalid(:\n    pass\n",
        source_path,
        is_benchmark=True,
    )

    assert result.status == "wrong_test"
    assert result.sandbox_result.returncode != 0


def test_mutation_known_answer_kills_known_mutants(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)

    result = MutationEvaluator(timeout_seconds=120).evaluate(
        KNOWN_COMPLETE_TESTS,
        source_path,
    )

    assert result.total_mutants > 0
    assert result.killed_mutants > 0
    assert result.killed_mutants == result.total_mutants
    assert result.survived_mutants == 0
    assert result.mutation_score == 1
    assert result.surviving_mutant_names == ()
    assert len(result.killed_mutant_names) == result.killed_mutants


def test_mutation_runs_xfail_assertions_instead_of_suppressing_failures(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path, "def answer():\n    return 42\n")
    tests = (
        "import pytest\n"
        "from testpilot_target import answer\n\n"
        "@pytest.mark.xfail(strict=True)\n"
        "def test_answer():\n"
        "    assert answer() == 42\n"
    )

    result = MutationEvaluator(timeout_seconds=120).evaluate(tests, source_path)

    assert result.total_mutants > 0
    assert result.killed_mutants == result.total_mutants


def test_mutation_known_answer_reports_surviving_mutants(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)
    test_code = (
        "from testpilot_target import classify\n\n"
        "def test_positive():\n"
        "    assert classify(1) == 'positive'\n"
    )

    result = MutationEvaluator(timeout_seconds=120).evaluate(test_code, source_path)

    assert result.survived_mutants > 0
    assert result.mutation_score < 1
    assert result.surviving_mutant_names
    assert len(result.surviving_mutant_diffs) == result.survived_mutants
    assert all(diff.strip() for _, diff in result.surviving_mutant_diffs)


def test_mutation_scores_all_mutants_as_surviving_when_tests_cover_no_code(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path, "def answer():\n    return 42\n")

    result = MutationEvaluator(timeout_seconds=120).evaluate(
        "def test_unrelated():\n    assert True\n",
        source_path,
    )

    assert result.total_mutants > 0
    assert result.killed_mutants == 0
    assert result.survived_mutants == result.total_mutants
    assert result.mutation_score == 0
    assert result.surviving_mutant_names
    assert len(result.surviving_mutant_diffs) == result.survived_mutants


def test_mutation_deselects_failing_test_before_scoring(tmp_path: Path) -> None:
    source_path = _source_file(tmp_path)
    tests = (
        "from testpilot_target import classify\n\n"
        "def test_wrong():\n"
        "    assert classify(1) == 'negative'\n\n"
        "def test_right():\n"
        "    assert classify(1) == 'positive'\n"
    )

    result = MutationEvaluator(timeout_seconds=120).evaluate(
        tests,
        source_path,
        ("tests/test_generated.py::test_wrong",),
    )

    assert result.total_mutants > 0
    assert result.killed_mutants > 0


def test_mutation_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="finite positive"):
        MutationEvaluator(float("nan"))


def test_mutation_rejects_suite_that_fails_on_original_source(
    tmp_path: Path,
) -> None:
    source_path = _source_file(tmp_path)
    test_code = (
        "from testpilot_target import classify\n\n"
        "def test_wrong_expectation():\n"
        "    assert classify(1) == 'negative'\n"
    )

    with pytest.raises(ValueError, match="must pass on the original source"):
        MutationEvaluator().evaluate(test_code, source_path)


def test_mutmut_failure_diagnostics_remove_spinner_and_keep_error_tail() -> None:
    result = subprocess.CompletedProcess(
        args=["mutmut", "run"],
        returncode=1,
        stdout=(
            "\r⠋ Generating mutants\r"
            "path/to/subject.py\n"
            "actual mutation failure\n"
        ),
        stderr="",
    )

    diagnostics = _subprocess_diagnostics(result)

    assert "actual mutation failure" in diagnostics
    assert "Generating mutants" not in diagnostics
