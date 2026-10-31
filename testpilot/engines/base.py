"""Shared engine data types."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from testpilot.analyzer import FunctionInfo


@dataclass(frozen=True)
class GeneratedSuite:
    """Represent a generated pytest suite and its generation metrics."""

    test_code: str
    engine_name: str
    wall_clock_seconds: float
    llm_tokens_used: int
    estimated_cost_usd: float
    rounds: int = 1
    wrong_test_count: int = 0
    needs_human_review_count: int = 0
    sampling_temperature: float | None = None
    sampling_seed: int | None = None


class TestGenerationEngine(Protocol):
    """Interface implemented by test generation engines."""

    def generate(
        self,
        function_info: FunctionInfo,
        source_path: Path,
    ) -> GeneratedSuite:
        """Generate tests for a function."""
