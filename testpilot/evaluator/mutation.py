"""Run mutmut against copied target source and generated tests."""

import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MutationResult:
    """Contain mutation totals and surviving mutant identifiers."""

    total_mutants: int
    killed_mutants: int
    survived_mutants: int
    timeout_mutants: int
    mutation_score: float
    surviving_mutant_names: tuple[str, ...]
    wall_clock_seconds: float
    stdout: str
    stderr: str


class MutationEvaluator:
    """Mutate and test a copied module using the native mutmut subprocess."""

    def __init__(self, timeout_seconds: float = 300.0) -> None:
        """Initialize mutation evaluation with a finite positive timeout."""
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a finite positive number")
        self.timeout_seconds = timeout_seconds

    def evaluate(self, test_code: str, source_path: Path) -> MutationResult:
        """Run mutmut in a disposable copy so target and cache stay isolated."""
        path = Path(source_path)
        if not path.is_file():
            raise FileNotFoundError(f"Source file does not exist: {path}")

        with tempfile.TemporaryDirectory(prefix="testpilot-mutmut-") as directory:
            working_directory = Path(directory)
            (working_directory / "testpilot_target.py").write_text(
                path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            tests_directory = working_directory / "tests"
            tests_directory.mkdir()
            (tests_directory / "test_generated.py").write_text(
                test_code,
                encoding="utf-8",
            )
            config_path = working_directory / "pyproject.toml"
            config_path.write_text(
                _mutmut_config(),
                encoding="utf-8",
            )

            started = time.perf_counter()
            run_result = _run_mutmut(
                ["run"],
                working_directory,
                self.timeout_seconds,
            )
            if run_result.returncode != 0:
                raise RuntimeError(
                    "mutmut failed: "
                    f"{run_result.stderr or run_result.stdout}"
                )

            stats_result = _run_mutmut(
                ["export-cicd-stats"],
                working_directory,
                _remaining_timeout(started, self.timeout_seconds),
            )
            if stats_result.returncode != 0:
                raise RuntimeError(
                    "mutmut could not export mutation statistics: "
                    f"{stats_result.stderr or stats_result.stdout}"
                )
            stats_path = working_directory / "mutants" / "mutmut-cicd-stats.json"
            try:
                stats = json.loads(stats_path.read_text(encoding="utf-8"))
                total = _read_count(stats, "total")
                killed = _read_count(stats, "killed")
                survived = _read_count(stats, "survived")
                timeout_count = _read_count(stats, "timeout")
                names = _surviving_names(
                    working_directory / "mutants" / "testpilot_target.py.meta"
                )
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RuntimeError("mutmut statistics were missing or invalid") from exc

            denominator = killed + survived
            score = killed / denominator if denominator else 0.0
            return MutationResult(
                total_mutants=total,
                killed_mutants=killed,
                survived_mutants=survived,
                timeout_mutants=timeout_count,
                mutation_score=score,
                surviving_mutant_names=names,
                wall_clock_seconds=time.perf_counter() - started,
                stdout=run_result.stdout + stats_result.stdout,
                stderr=run_result.stderr + stats_result.stderr,
            )


def _mutmut_config() -> str:
    """Configure one copied module and pytest suite; disable macOS setproctitle."""
    return """\
[tool.mutmut]
source_paths = ["testpilot_target.py"]
pytest_add_cli_args_test_selection = ["tests/test_generated.py"]
use_setproctitle = false
"""


def _run_mutmut(
    arguments: list[str],
    working_directory: Path,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        [sys.executable, "-m", "mutmut", *arguments],
        cwd=working_directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        raise TimeoutError(
            f"mutmut {arguments[0]} exceeded {timeout_seconds:g} seconds"
        ) from exc
    return subprocess.CompletedProcess(
        args=process.args,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _read_count(stats: dict[str, object], key: str) -> int:
    value = stats[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid mutmut count: {key}")
    return value


def _surviving_names(metadata_path: Path) -> tuple[str, ...]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    exit_codes = metadata.get("exit_code_by_key")
    if not isinstance(exit_codes, dict):
        raise ValueError("mutmut metadata has no mutant exit codes")
    return tuple(
        sorted(
            name
            for name, exit_code in exit_codes.items()
            if isinstance(name, str) and exit_code == 0
        )
    )


def _remaining_timeout(started: float, timeout_seconds: float) -> float:
    remaining = timeout_seconds - (time.perf_counter() - started)
    if remaining <= 0:
        raise TimeoutError("mutmut evaluation exceeded its timeout")
    return remaining
