"""Measure line and branch coverage in an isolated pytest subprocess."""

import json
import math
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from testpilot.sandbox.environment import isolated_subprocess_environment


@dataclass(frozen=True)
class CoverageResult:
    """Contain test outcomes and line/branch coverage measurements."""

    tests_run: int
    passed: int
    failed: int
    errors: int
    skipped: int
    line_covered: int
    line_total: int
    line_percent: float
    branch_covered: int
    branch_total: int
    branch_percent: float
    uncovered_lines: tuple[int, ...]
    uncovered_branches: tuple[tuple[int, int], ...]
    returncode: int
    wall_clock_seconds: float
    stdout: str
    stderr: str


class CoverageEvaluator:
    """Run pytest and coverage.py against copied source and generated tests."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        """Initialize coverage evaluation with a finite positive timeout."""
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a finite positive number")
        self.timeout_seconds = timeout_seconds

    def evaluate(self, test_code: str, source_path: Path) -> CoverageResult:
        """Measure line and branch coverage without importing source in-process."""
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        with tempfile.TemporaryDirectory(prefix="testpilot-coverage-") as directory:
            working_directory = Path(directory)
            (working_directory / "testpilot_target.py").write_text(
                path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            tests_directory = working_directory / "tests"
            tests_directory.mkdir()
            test_path = tests_directory / "test_generated.py"
            test_path.write_text(test_code, encoding="utf-8")
            junit_path = working_directory / "pytest-report.xml"
            coverage_path = working_directory / "coverage.json"
            command = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--branch",
                "--source=testpilot_target",
                "-m",
                "pytest",
                "-q",
                f"--junitxml={junit_path}",
                str(test_path),
            ]

            started = time.perf_counter()
            try:
                test_process = subprocess.run(
                    command,
                    cwd=working_directory,
                    capture_output=True,
                    text=True,
                    env=isolated_subprocess_environment(),
                    timeout=self.timeout_seconds,
                    check=False,
                )
                report_process = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "coverage",
                        "json",
                        "-o",
                        str(coverage_path),
                    ],
                    cwd=working_directory,
                    capture_output=True,
                    text=True,
                    env=isolated_subprocess_environment(),
                    timeout=_remaining_timeout(started, self.timeout_seconds),
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError(
                    f"Coverage evaluation exceeded {self.timeout_seconds:g} seconds"
                ) from exc

            if test_process.returncode not in (0, 1):
                raise RuntimeError(
                    "Coverage pytest process failed unexpectedly: "
                    f"{test_process.stderr or test_process.stdout}"
                )
            if report_process.returncode != 0:
                raise RuntimeError(
                    "Could not produce coverage JSON: "
                    f"{report_process.stderr or report_process.stdout}"
                )

            try:
                report = json.loads(coverage_path.read_text(encoding="utf-8"))
                file_report = report["files"]["testpilot_target.py"]
                summary = file_report["summary"]
                junit_counts = _junit_counts(junit_path)
                line_total = summary["num_statements"]
                line_covered = summary["covered_lines"]
                line_percent = (
                    100.0 * line_covered / line_total if line_total else 100.0
                )
                branch_total = summary["num_branches"]
                branch_covered = summary["covered_branches"]
                branch_percent = (
                    100.0 * branch_covered / branch_total if branch_total else 100.0
                )
                return CoverageResult(
                    tests_run=junit_counts[0],
                    passed=junit_counts[1],
                    failed=junit_counts[2],
                    errors=junit_counts[3],
                    skipped=junit_counts[4],
                    line_covered=line_covered,
                    line_total=line_total,
                    line_percent=line_percent,
                    branch_covered=branch_covered,
                    branch_total=branch_total,
                    branch_percent=branch_percent,
                    uncovered_lines=tuple(file_report["missing_lines"]),
                    uncovered_branches=tuple(
                        (branch[0], branch[1])
                        for branch in file_report["missing_branches"]
                    ),
                    returncode=test_process.returncode,
                    wall_clock_seconds=time.perf_counter() - started,
                    stdout=test_process.stdout,
                    stderr=test_process.stderr,
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("Coverage report was incomplete or invalid") from exc


def _junit_counts(report_path: Path) -> tuple[int, int, int, int, int]:
    if not report_path.is_file():
        return (0, 0, 0, 0, 0)
    test_cases = ET.parse(report_path).getroot().findall(".//testcase")
    failed = sum(case.find("failure") is not None for case in test_cases)
    errors = sum(case.find("error") is not None for case in test_cases)
    skipped = sum(case.find("skipped") is not None for case in test_cases)
    passed = len(test_cases) - failed - errors - skipped
    return len(test_cases), passed, failed, errors, skipped


def _remaining_timeout(started: float, timeout_seconds: float) -> float:
    remaining = timeout_seconds - (time.perf_counter() - started)
    if remaining <= 0:
        raise subprocess.TimeoutExpired("coverage json", timeout_seconds)
    return remaining
