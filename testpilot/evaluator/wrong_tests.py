"""Classify failures against benchmark and user-provided implementations."""

from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from testpilot.sandbox import SandboxResult, SandboxRunner
from testpilot.sandbox import passing_test_selection

WrongTestStatus = Literal[
    "passed",
    "wrong_test",
    "needs_human_review",
    "timed_out",
]


@dataclass(frozen=True)
class WrongTestResult:
    """Represent generated-test correctness without overclaiming user-code bugs."""

    status: WrongTestStatus
    failing_tests: int
    sandbox_result: SandboxResult
    explanation: str
    expected_failure_count: int = 0


class WrongTestDetector:
    """Run generated tests against a known answer or user implementation."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        """Initialize with a sandbox runner and its subprocess timeout."""
        self._runner = SandboxRunner(timeout_seconds)

    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        is_benchmark: bool,
    ) -> WrongTestResult:
        """Classify failures against canonical benchmark or unknown user code."""
        result = self._runner.run(test_code, source_path)
        if result.timed_out:
            return WrongTestResult(
                status="timed_out",
                failing_tests=0,
                sandbox_result=result,
                explanation="The test suite timed out; its correctness is undetermined.",
            )

        selection = passing_test_selection(test_code, result.test_outcomes)
        if selection is None:
            failing_tests = result.failed + result.errors
            expected_failure_count = 0
        else:
            failing_tests = selection.wrong_test_count
            expected_failure_count = selection.expected_failure_count

        only_expected_failures = (
            expected_failure_count > 0
            and result.returncode == 1
            and result.failed + result.errors == expected_failure_count
        )
        if failing_tests == 0 and (
            result.returncode == 0 or only_expected_failures
        ):
            return WrongTestResult(
                status="passed",
                failing_tests=0,
                sandbox_result=result,
                explanation=(
                    "All non-xfail generated tests passed; xfail-marked tests "
                    "are reported separately and excluded from scoring."
                ),
                expected_failure_count=expected_failure_count,
            )
        if is_benchmark:
            return WrongTestResult(
                status="wrong_test",
                failing_tests=failing_tests,
                sandbox_result=result,
                explanation=(
                    "The generated suite failed against the canonical benchmark "
                    "solution and is classified as a wrong test suite."
                ),
                expected_failure_count=expected_failure_count,
            )
        return WrongTestResult(
            status="needs_human_review",
            failing_tests=failing_tests,
            sandbox_result=result,
            explanation=(
                "The generated suite failed against user code; this may indicate "
                "a wrong test or a real bug and needs human review."
            ),
            expected_failure_count=expected_failure_count,
        )
