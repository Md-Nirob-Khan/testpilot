"""Tests for safe subprocess execution of generated tests."""

from pathlib import Path

import pytest

from testpilot.sandbox import SandboxRunner


def test_sandbox_runs_passing_generated_tests(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    test_code = (
        "from testpilot_target import add\n\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n"
    )

    result = SandboxRunner().run(test_code, source_path)

    assert result.tests_run == 1
    assert result.passed == 1
    assert result.failed == result.errors == result.skipped == 0
    assert result.returncode == 0
    assert not result.timed_out


def test_sandbox_reports_assertion_failures(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def answer():\n    return 42\n", encoding="utf-8")

    result = SandboxRunner().run(
        "from testpilot_target import answer\n"
        "def test_answer():\n"
        "    assert answer() == 0\n",
        source_path,
    )

    assert result.tests_run == 1
    assert result.failed == 1
    assert result.returncode != 0
    assert "AssertionError" in result.stdout


def test_sandbox_enforces_timeout(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = "import time\n\ndef test_slow():\n    time.sleep(2)\n"

    result = SandboxRunner(timeout_seconds=0.1).run(test_code, source_path)

    assert result.timed_out
    assert result.wall_clock_seconds < 2
    assert result.returncode is None


def test_sandbox_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="Timeout must be a finite positive number"):
        SandboxRunner(timeout_seconds=0)


@pytest.mark.parametrize("timeout_seconds", [float("inf"), float("nan")])
def test_sandbox_rejects_non_finite_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="Timeout must be a finite positive number"):
        SandboxRunner(timeout_seconds=timeout_seconds)


def test_sandbox_requires_existing_source_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        SandboxRunner().run("def test_empty():\n    pass\n", tmp_path / "missing.py")
