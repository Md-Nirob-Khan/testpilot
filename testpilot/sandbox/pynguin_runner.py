"""Run Pynguin in a temporary directory and a dedicated Python environment."""

import math
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from testpilot.sandbox.environment import isolated_subprocess_environment


@dataclass(frozen=True)
class PynguinResult:
    """Capture a generated suite and Pynguin's elapsed time."""

    test_code: str
    wall_clock_seconds: float


class PynguinExecutionError(RuntimeError):
    """Raised when Pynguin fails to generate a test suite."""


class PynguinSubprocessRunner:
    """Execute Pynguin in a temporary directory with a strict timeout."""

    def __init__(
        self,
        python_executable: Path | None = None,
        timeout_seconds: float = 120.0,
        search_time_seconds: int = 30,
        seed: int = 42,
    ) -> None:
        """Initialize the Pynguin executable and finite generation limits."""
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Timeout must be a finite positive number")
        if (
            isinstance(search_time_seconds, bool)
            or not isinstance(search_time_seconds, int)
            or search_time_seconds <= 0
        ):
            raise ValueError("Search time must be a positive integer")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("Seed must be an integer")

        if python_executable is None:
            repository_root = Path(__file__).parents[2]
            executable_name = (
                "python.exe" if os.name == "nt" else "python"
            )
            executable_directory = (
                "Scripts" if os.name == "nt" else "bin"
            )
            python_executable = (
                repository_root
                / ".venv-pynguin"
                / executable_directory
                / executable_name
            )

        self.python_executable = Path(os.path.abspath(python_executable))
        self.timeout_seconds = timeout_seconds
        self.search_time_seconds = search_time_seconds
        self.seed = seed

    def generate(
        self,
        source_path: Path,
        function_name: str | None = None,
    ) -> PynguinResult:
        """Generate tests for a copied source module in an isolated subprocess."""
        source = Path(source_path)
        if not source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {source}")
        if not self.python_executable.is_file():
            raise FileNotFoundError(
                f"Pynguin Python environment does not exist: "
                f"{self.python_executable}"
            )

        with tempfile.TemporaryDirectory(prefix="testpilot-pynguin-") as directory:
            working_directory = Path(directory)
            target_path = working_directory / "testpilot_target.py"
            target_path.write_bytes(source.read_bytes())
            output_directory = working_directory / "generated"
            output_directory.mkdir()
            command = [
                str(self.python_executable),
                "-m",
                "pynguin",
                "--project_path",
                str(working_directory),
                "--module-name",
                "testpilot_target",
            ]
            if function_name is not None:
                if not function_name.strip():
                    raise ValueError("Function name must not be empty")
                command.extend(["--only-cover", function_name])
            command.extend(
                [
                    "--output_path",
                    str(output_directory),
                    "--maximum_search_time",
                    str(self.search_time_seconds),
                    "--seed",
                    str(self.seed),
                ]
            )
            environment = isolated_subprocess_environment()
            environment["PYNGUIN_DANGER_AWARE"] = "1"

            started = time.perf_counter()
            completed = _run_with_timeout(
                command,
                cwd=working_directory,
                env=environment,
                timeout_seconds=self.timeout_seconds,
            )
            elapsed = time.perf_counter() - started

            if completed.returncode != 0:
                details = completed.stderr or completed.stdout
                raise PynguinExecutionError(
                    f"Pynguin exited with status {completed.returncode}: "
                    f"{details.strip() or '(no output)'}"
                )

            generated_path = output_directory / "test_testpilot_target.py"
            if not generated_path.is_file():
                details = completed.stderr or completed.stdout
                raise PynguinExecutionError(
                    "Pynguin completed without generating "
                    f"{generated_path.name}: {details.strip() or '(no output)'}"
                )

            return PynguinResult(
                test_code=generated_path.read_text(encoding="utf-8"),
                wall_clock_seconds=elapsed,
            )


def _run_with_timeout(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    """Run Pynguin and terminate its process group if the timeout expires."""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=os.name == "posix",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        stdout, stderr = process.communicate()
        details = stderr or stdout or str(exc)
        raise TimeoutError(
            f"Pynguin exceeded its {timeout_seconds:g}-second timeout: "
            f"{details.strip()}"
        ) from exc

    return subprocess.CompletedProcess(
        command,
        process.returncode,
        stdout,
        stderr,
    )
