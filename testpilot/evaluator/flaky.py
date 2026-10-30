"""Repeat generated suites and identify tests with changing outcomes."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from testpilot.sandbox import SandboxResult, SandboxRunner


@dataclass(frozen=True)
class TestFlakiness:
    """Report one test's observed outcome on each run."""

    test_name: str
    outcomes: tuple[str, ...]


@dataclass(frozen=True)
class FlakyTestResult:
    """Summarize repeated suite runs and unstable test outcomes."""

    run_count: int
    flaky_test_names: tuple[str, ...]
    tests: tuple[TestFlakiness, ...]
    timed_out_runs: tuple[int, ...]
    inconclusive_runs: tuple[int, ...]


class _SandboxRunner(Protocol):
    def run(self, test_code: str, source_path: Path) -> SandboxResult:
        """Execute one full suite and return collected test outcomes."""


class FlakyTestChecker:
    """Run each suite three times by default in isolated sandbox processes."""

    def __init__(
        self,
        run_count: int = 3,
        timeout_seconds: float = 30.0,
        runner: _SandboxRunner | None = None,
    ) -> None:
        """Initialize a repeat count and finite per-run timeout."""
        if (
            isinstance(run_count, bool)
            or not isinstance(run_count, int)
            or run_count < 2
        ):
            raise ValueError("Run count must be an integer of at least two")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a finite positive number")
        self.run_count = run_count
        self._runner = runner or SandboxRunner(timeout_seconds)

    def evaluate(self, test_code: str, source_path: Path) -> FlakyTestResult:
        """Run the full suite repeatedly and flag test outcome changes."""
        run_results = [
            self._runner.run(test_code, source_path)
            for _ in range(self.run_count)
        ]
        timed_out_runs = tuple(
            index
            for index, result in enumerate(run_results, start=1)
            if result.timed_out
        )
        inconclusive_runs = tuple(
            index
            for index, result in enumerate(run_results, start=1)
            if not result.timed_out and not result.test_outcomes
        )
        observed_names = sorted(
            {
                outcome.name
                for result in run_results
                for outcome in result.test_outcomes
            }
        )

        tests: list[TestFlakiness] = []
        flaky_names: list[str] = []
        for test_name in observed_names:
            outcomes: list[str] = []
            for result in run_results:
                status_by_name = {
                    outcome.name: outcome.status
                    for outcome in result.test_outcomes
                }
                if result.timed_out:
                    outcomes.append("timed out")
                elif not result.test_outcomes:
                    outcomes.append("no tests observed")
                else:
                    outcomes.append(status_by_name.get(test_name, "not collected"))
            observation = TestFlakiness(test_name, tuple(outcomes))
            tests.append(observation)
            comparable_outcomes = {
                outcome
                for outcome in outcomes
                if outcome not in ("timed out", "no tests observed", "not collected")
            }
            if len(comparable_outcomes) > 1 or (
                "not collected" in outcomes and comparable_outcomes
            ):
                flaky_names.append(test_name)

        return FlakyTestResult(
            run_count=self.run_count,
            flaky_test_names=tuple(flaky_names),
            tests=tuple(tests),
            timed_out_runs=timed_out_runs,
            inconclusive_runs=inconclusive_runs,
        )
