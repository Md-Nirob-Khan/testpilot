"""Classify failures against benchmark and user-provided implementations."""

from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from testpilot.sandbox import SandboxResult, SandboxRunner

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

        failing_tests = result.failed + result.errors
        if failing_tests == 0 and result.returncode == 0:
            return WrongTestResult(
                status="passed",
                failing_tests=0,
                sandbox_result=result,
                explanation="All generated tests passed on the supplied implementation.",
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
            )
        return WrongTestResult(
            status="needs_human_review",
            failing_tests=failing_tests,
            sandbox_result=result,
            explanation=(
                "The generated suite failed against user code; this may indicate "
                "a wrong test or a real bug and needs human review."
            ),
        )
