"""Iteratively improve generated tests using isolated evaluator feedback."""

import time
from pathlib import Path
from typing import Protocol

from testpilot.analyzer import FunctionInfo
from testpilot.engines.base import GeneratedSuite
from testpilot.engines.llm_engine import (
    _SYSTEM_PROMPT,
    _strip_markdown_fence,
    build_test_prompt,
)
from testpilot.evaluator import CoverageEvaluator, MutationEvaluator, WrongTestDetector
from testpilot.evaluator.coverage_evaluator import CoverageResult
from testpilot.evaluator.mutation import MutationResult
from testpilot.evaluator.wrong_tests import WrongTestResult
from testpilot.llm import LLMProvider


class _CoverageEvaluator(Protocol):
    def evaluate(self, test_code: str, source_path: Path) -> CoverageResult:
        """Evaluate line and branch coverage."""


class _MutationEvaluator(Protocol):
    def evaluate(self, test_code: str, source_path: Path) -> MutationResult:
        """Evaluate mutation score."""


class _WrongTestDetector(Protocol):
    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        is_benchmark: bool,
    ) -> WrongTestResult:
        """Evaluate raw generated tests against their original source."""


class AgentEngine:
    """Generate, evaluate, and iteratively improve a pytest suite."""

    def __init__(
        self,
        provider: LLMProvider,
        max_rounds: int = 3,
        is_benchmark: bool = False,
        coverage_evaluator: _CoverageEvaluator | None = None,
        mutation_evaluator: _MutationEvaluator | None = None,
        wrong_test_detector: _WrongTestDetector | None = None,
    ) -> None:
        """Initialize the provider, round limit, and evaluation components."""
        if (
            isinstance(max_rounds, bool)
            or not isinstance(max_rounds, int)
            or max_rounds < 1
        ):
            raise ValueError("max_rounds must be a positive integer")
        self._provider = provider
        self._max_rounds = max_rounds
        self._is_benchmark = is_benchmark
        self._coverage_evaluator = coverage_evaluator or CoverageEvaluator()
        self._mutation_evaluator = mutation_evaluator or MutationEvaluator()
        self._wrong_test_detector = wrong_test_detector or WrongTestDetector()

    def generate(
        self,
        function_info: FunctionInfo,
        source_path: Path,
    ) -> GeneratedSuite:
        """Return the best passing generated suite within the configured rounds."""
        started = time.perf_counter()
        best_suite: GeneratedSuite | None = None
        best_score = -1.0
        previous_score: float | None = None
        previous_tests: str | None = None
        feedback: str | None = None
        tokens_used = 0
        estimated_cost = 0.0
        wrong_test_count = 0
        needs_human_review_count = 0
        latest_suite: GeneratedSuite | None = None
        rounds = 0

        for round_number in range(1, self._max_rounds + 1):
            user_prompt = build_test_prompt(
                function_info,
                source_path,
                feedback=feedback,
                previous_tests=previous_tests,
            )
            response = self._provider.complete(_SYSTEM_PROMPT, user_prompt)
            test_code = _strip_markdown_fence(response.content)
            if not test_code.strip():
                raise ValueError("The LLM provider returned an empty test suite")

            rounds = round_number
            tokens_used += response.total_tokens
            estimated_cost += response.estimated_cost_usd

            correctness = self._wrong_test_detector.evaluate(
                test_code,
                source_path,
                is_benchmark=self._is_benchmark,
            )
            if correctness.status == "wrong_test":
                wrong_test_count += correctness.failing_tests
            elif correctness.status == "needs_human_review":
                needs_human_review_count += correctness.failing_tests

            coverage = None
            mutation = None
            if correctness.status == "passed":
                coverage = self._coverage_evaluator.evaluate(test_code, source_path)
                mutation = self._mutation_evaluator.evaluate(test_code, source_path)

            candidate = GeneratedSuite(
                test_code=test_code,
                engine_name="agent-llm",
                wall_clock_seconds=time.perf_counter() - started,
                llm_tokens_used=tokens_used,
                estimated_cost_usd=estimated_cost,
                rounds=rounds,
                wrong_test_count=wrong_test_count,
                needs_human_review_count=needs_human_review_count,
            )
            latest_suite = candidate

            if mutation is not None:
                score = mutation.mutation_score
                if score > best_score:
                    best_score = score
                    best_suite = candidate
                if previous_score is not None and score <= previous_score:
                    break
                previous_score = score

            previous_tests = test_code
            feedback = _format_feedback(correctness, coverage, mutation)

        selected_suite = best_suite or latest_suite
        if selected_suite is None:
            raise RuntimeError("Agent engine did not generate a test suite")
        return GeneratedSuite(
            test_code=selected_suite.test_code,
            engine_name=selected_suite.engine_name,
            wall_clock_seconds=time.perf_counter() - started,
            llm_tokens_used=tokens_used,
            estimated_cost_usd=estimated_cost,
            rounds=rounds,
            wrong_test_count=wrong_test_count,
            needs_human_review_count=needs_human_review_count,
        )


def _format_feedback(
    correctness: WrongTestResult,
    coverage: CoverageResult | None,
    mutation: MutationResult | None,
) -> str:
    """Format evaluator observations for the next generation attempt."""
    if correctness.status != "passed":
        sandbox_result = correctness.sandbox_result
        details = sandbox_result.stdout or sandbox_result.stderr
        return (
            f"Wrong-test status: {correctness.status}\n"
            f"Failing tests: {correctness.failing_tests}\n"
            f"Explanation: {correctness.explanation}\n"
            f"Raw pytest output:\n{details or '(no output)'}"
        )

    if coverage is None or mutation is None:
        raise RuntimeError("Passing generated tests require coverage and mutation results")

    return "\n".join(
        [
            "Wrong-test status: passed",
            (
                f"Line coverage: {coverage.line_percent:.1f}% "
                f"({coverage.line_covered}/{coverage.line_total})"
            ),
            f"Uncovered source lines: {coverage.uncovered_lines or 'none'}",
            (
                f"Branch coverage: {coverage.branch_percent:.1f}% "
                f"({coverage.branch_covered}/{coverage.branch_total})"
            ),
            f"Uncovered branches: {coverage.uncovered_branches or 'none'}",
            (
                f"Mutation score: {mutation.mutation_score:.1%} "
                f"({mutation.killed_mutants}/{mutation.total_mutants} "
                f"killed; {mutation.survived_mutants} survived)"
            ),
            (
                "Surviving mutants: "
                f"{mutation.surviving_mutant_names or 'none'}"
            ),
        ]
    )
