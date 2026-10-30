"""Run generated pytest suites outside the TestPilot process."""

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
class TestOutcome:
    """Represent one collected pytest test and its result."""

    __test__ = False

    name: str
    status: str


@dataclass(frozen=True)
class SandboxResult:
    """Capture pytest results and subprocess output."""

    tests_run: int
    passed: int
    failed: int
    errors: int
    skipped: int
    returncode: int | None
    timed_out: bool
    wall_clock_seconds: float
    stdout: str
    stderr: str
    test_outcomes: tuple[TestOutcome, ...] = ()


class SandboxRunner:
    """Execute a generated suite in a temporary directory with a timeout."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        """Initialize the runner with a finite positive timeout."""
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a finite positive number")
        self.timeout_seconds = timeout_seconds

    def run(self, test_code: str, source_path: Path) -> SandboxResult:
        """Run pytest against a copied source file in a child process."""
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        with tempfile.TemporaryDirectory(prefix="testpilot-sandbox-") as temporary_dir:
            working_directory = Path(temporary_dir)
            (working_directory / "testpilot_target.py").write_text(
                path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (working_directory / "test_generated.py").write_text(
                test_code,
                encoding="utf-8",
            )
            report_path = working_directory / "pytest-report.xml"
            command = [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                f"--junitxml={report_path}",
                str(working_directory / "test_generated.py"),
            ]

            started = time.perf_counter()
            try:
                completed = subprocess.run(
                    command,
                    cwd=working_directory,
                    capture_output=True,
                    text=True,
                    env=isolated_subprocess_environment(),
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                elapsed = time.perf_counter() - started
                return SandboxResult(
                    tests_run=0,
                    passed=0,
                    failed=0,
                    errors=0,
                    skipped=0,
                    returncode=None,
                    timed_out=True,
                    wall_clock_seconds=elapsed,
                    stdout=_output_text(exc.stdout),
                    stderr=_output_text(exc.stderr),
                )

            elapsed = time.perf_counter() - started
            counts, outcomes = _read_junit_report(report_path)
            return SandboxResult(
                tests_run=counts[0],
                passed=counts[1],
                failed=counts[2],
                errors=counts[3],
                skipped=counts[4],
                returncode=completed.returncode,
                timed_out=False,
                wall_clock_seconds=elapsed,
                stdout=completed.stdout,
                stderr=completed.stderr,
                test_outcomes=outcomes,
            )


def _read_junit_report(
    report_path: Path,
) -> tuple[tuple[int, int, int, int, int], tuple[TestOutcome, ...]]:
    """Count test outcomes from pytest's JUnit XML report."""
    if not report_path.is_file():
        return (0, 0, 0, 0, 0), ()
    root = ET.parse(report_path).getroot()
    test_cases = root.findall(".//testcase")
    outcomes = tuple(
        TestOutcome(
            name="::".join(
                item for item in (case.get("classname"), case.get("name")) if item
            ),
            status=_test_case_status(case),
        )
        for case in test_cases
    )
    failed = sum(outcome.status == "failed" for outcome in outcomes)
    errors = sum(outcome.status == "error" for outcome in outcomes)
    skipped = sum(outcome.status == "skipped" for outcome in outcomes)
    passed = len(test_cases) - failed - errors - skipped
    return (len(test_cases), passed, failed, errors, skipped), outcomes


def _test_case_status(test_case: ET.Element) -> str:
    """Return one normalized outcome for a JUnit testcase element."""
    for tag, status in (
        ("failure", "failed"),
        ("error", "error"),
        ("skipped", "skipped"),
    ):
        if test_case.find(tag) is not None:
            return status
    return "passed"


def _output_text(output: str | bytes | None) -> str:
    """Convert captured timeout output to text."""
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output
