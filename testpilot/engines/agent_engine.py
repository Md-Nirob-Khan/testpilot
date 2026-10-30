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
from testpilot.sandbox import passing_test_selection


class _CoverageEvaluator(Protocol):
    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        deselected_test_ids: tuple[str, ...] = (),
    ) -> CoverageResult:
        """Evaluate line and branch coverage."""


class _MutationEvaluator(Protocol):
    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        deselected_test_ids: tuple[str, ...] = (),
    ) -> MutationResult:
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
            selection = passing_test_selection(
                test_code,
                correctness.sandbox_result.test_outcomes,
            )
            if selection is not None:
                scoring_test_count = selection.passing_test_count
                deselected_coverage = selection.for_test_file(
                    "tests/test_generated.py"
                )
                deselected_mutation = deselected_coverage
            else:
                scoring_test_count = 0
                deselected_coverage = ()
                deselected_mutation = ()
            evaluator_errors: list[str] = []
            if scoring_test_count:
                try:
                    coverage = self._coverage_evaluator.evaluate(
                        test_code,
                        source_path,
                        deselected_coverage,
                    )
                except Exception as exc:
                    evaluator_errors.append(
                        f"Coverage evaluation failed: {_format_error(exc)}"
                    )
                try:
                    mutation = self._mutation_evaluator.evaluate(
                        test_code,
                        source_path,
                        deselected_mutation,
                    )
                except Exception as exc:
                    evaluator_errors.append(
                        f"Mutation evaluation failed: {_format_error(exc)}"
                    )

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
            feedback = _format_feedback(
                correctness,
                coverage,
                mutation,
                evaluator_errors,
            )

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
    evaluator_errors: list[str] | None = None,
) -> str:
    """Format evaluator observations for the next generation attempt."""
    feedback = [
        f"Wrong-test status: {correctness.status}",
        f"Failing tests: {correctness.failing_tests}",
        f"Xfail-marked tests excluded: {correctness.expected_failure_count}",
        f"Explanation: {correctness.explanation}",
    ]
    if correctness.failing_tests:
        sandbox_result = correctness.sandbox_result
        details = sandbox_result.stdout or sandbox_result.stderr
        feedback.append(f"Raw pytest output:\n{details or '(no output)'}")
    if coverage is None:
        feedback.append("Coverage: unavailable")
    else:
        feedback.extend(
            [
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
            ]
        )
    if mutation is None:
        feedback.append("Mutation score: unavailable")
    else:
        feedback.extend(
            [
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
    feedback.extend(evaluator_errors or [])
    return "\n".join(feedback)


def _format_error(error: Exception) -> str:
    """Format evaluator errors for model feedback."""
    message = " ".join(str(error).split()) or "(no details)"
    return f"{type(error).__name__}: {message}"
