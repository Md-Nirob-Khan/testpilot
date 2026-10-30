"""Tests for repeated suite execution and flaky-test detection."""

from pathlib import Path

import pytest

from testpilot.evaluator import FlakyTestChecker
from testpilot.sandbox import SandboxResult, TestOutcome


class _SequenceRunner:
    def __init__(self, results: list[SandboxResult]) -> None:
        self.results = iter(results)
        self.calls = 0

    def run(self, test_code: str, source_path: Path) -> SandboxResult:
        self.calls += 1
        return next(self.results)


def _result(*outcomes: TestOutcome, timed_out: bool = False) -> SandboxResult:
    passed = sum(outcome.status == "passed" for outcome in outcomes)
    failed = sum(outcome.status == "failed" for outcome in outcomes)
    errors = sum(outcome.status == "error" for outcome in outcomes)
    skipped = sum(outcome.status == "skipped" for outcome in outcomes)
    return SandboxResult(
        tests_run=len(outcomes),
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        returncode=None if timed_out else (0 if failed == errors == 0 else 1),
        timed_out=timed_out,
        wall_clock_seconds=0.1,
        stdout="",
        stderr="",
        test_outcomes=outcomes,
    )


def test_flaky_checker_flags_only_tests_with_changing_results(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        [
            _result(
                TestOutcome("test_module::test_stable", "passed"),
                TestOutcome("test_module::test_unstable", "passed"),
            ),
            _result(
                TestOutcome("test_module::test_stable", "passed"),
                TestOutcome("test_module::test_unstable", "failed"),
            ),
            _result(
                TestOutcome("test_module::test_stable", "passed"),
                TestOutcome("test_module::test_unstable", "passed"),
            ),
        ]
    )
    checker = FlakyTestChecker(runner=runner)

    result = checker.evaluate("def test_generated(): pass", tmp_path / "source.py")

    assert runner.calls == 3
    assert result.run_count == 3
    assert result.flaky_test_names == ("test_module::test_unstable",)
    assert result.timed_out_runs == ()


def test_flaky_checker_does_not_call_timeout_a_flaky_test(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        [
            _result(TestOutcome("test_module::test_slow", "passed")),
            _result(timed_out=True),
            _result(TestOutcome("test_module::test_slow", "passed")),
        ]
    )

    result = FlakyTestChecker(runner=runner).evaluate(
        "def test_slow(): pass",
        tmp_path / "source.py",
    )

    assert result.flaky_test_names == ()
    assert result.timed_out_runs == (2,)
    assert result.tests[0].outcomes == ("passed", "timed out", "passed")


def test_flaky_checker_reports_runs_without_test_outcomes_as_inconclusive(
    tmp_path: Path,
) -> None:
    runner = _SequenceRunner(
        [
            _result(),
            _result(TestOutcome("test_module::test_stable", "passed")),
            _result(TestOutcome("test_module::test_stable", "passed")),
        ]
    )

    result = FlakyTestChecker(runner=runner).evaluate(
        "invalid test suite",
        tmp_path / "source.py",
    )

    assert result.flaky_test_names == ()
    assert result.inconclusive_runs == (1,)
    assert result.tests[0].outcomes == (
        "no tests observed",
        "passed",
        "passed",
    )


@pytest.mark.parametrize("run_count", [0, 1, True, 2.5])
def test_flaky_checker_rejects_invalid_run_count(run_count: int) -> None:
    with pytest.raises(ValueError, match="Run count must be an integer"):
        FlakyTestChecker(run_count=run_count)
