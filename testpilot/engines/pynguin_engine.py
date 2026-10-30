"""Search-based test generation using Pynguin."""

from pathlib import Path

from testpilot.analyzer import FunctionInfo
from testpilot.engines.base import GeneratedSuite
from testpilot.sandbox.pynguin_runner import PynguinSubprocessRunner


class PynguinEngine:
    """Generate a pytest suite with the isolated Pynguin environment."""

    def __init__(self, runner: PynguinSubprocessRunner | None = None) -> None:
        """Initialize the subprocess runner."""
        self._runner = runner or PynguinSubprocessRunner()

    def generate(
        self,
        function_info: FunctionInfo,
        source_path: Path,
    ) -> GeneratedSuite:
        """Generate tests for the module containing the requested function."""
        if not function_info.name:
            raise ValueError("Function name must not be empty")
        result = self._runner.generate(source_path, function_info.name)
        return GeneratedSuite(
            test_code=result.test_code,
            engine_name="pynguin",
            wall_clock_seconds=result.wall_clock_seconds,
            llm_tokens_used=0,
            estimated_cost_usd=0.0,
        )
