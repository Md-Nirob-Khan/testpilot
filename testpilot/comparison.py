"""Generate and evaluate selected engines for dashboard comparisons."""

import time
from pathlib import Path
from typing import Callable, Mapping, Sequence

from testpilot.analyzer import FunctionInfo
from testpilot.engines import AgentEngine, PynguinEngine, SingleShotEngine
from testpilot.engines.base import TestGenerationEngine
from testpilot.evaluator import (
    CoverageEvaluator,
    FlakyTestChecker,
    MutationEvaluator,
    WrongTestDetector,
    explain_mutants,
)
from testpilot.llm import LLMProvider, create_provider
from testpilot.merge import BestOfMerger
from testpilot.sandbox import passing_test_selection
from testpilot.storage import EngineRun

ENGINE_NAMES = ("Single-shot LLM", "Agent LLM", "Pynguin")
_ENGINE_KEYS = {
    "Single-shot LLM": "single-shot-llm",
    "Agent LLM": "agent-llm",
    "Pynguin": "pynguin",
}


def compare_functions(
    source_path: Path,
    functions: Sequence[FunctionInfo],
    engine_names: Sequence[str],
    engine_factories: Mapping[str, Callable[[], TestGenerationEngine]] | None = None,
    provider_factory: Callable[[], LLMProvider] = create_provider,
) -> list[EngineRun]:
    """Generate and evaluate every selected function-engine combination."""
    unknown_engines = set(engine_names).difference(ENGINE_NAMES)
    if unknown_engines:
        raise ValueError(f"Unknown engines: {', '.join(sorted(unknown_engines))}")
    if not functions:
        raise ValueError("Select at least one function")
    if not engine_names:
        raise ValueError("Select at least one engine")

    custom_factories = engine_factories or {}
    coverage_evaluator = CoverageEvaluator()
    mutation_evaluator = MutationEvaluator()
    wrong_test_detector = WrongTestDetector()
    flaky_test_checker = FlakyTestChecker()
    provider: LLMProvider | None = None
    engines: dict[str, TestGenerationEngine | Exception] = {}
    results: list[EngineRun] = []

    def get_provider() -> LLMProvider:
        nonlocal provider
        if provider is None:
            provider = provider_factory()
        return provider

    for engine_name in engine_names:
        try:
            if engine_name in custom_factories:
                engine = custom_factories[engine_name]()
            elif engine_name == "Single-shot LLM":
                engine = SingleShotEngine(get_provider())
            elif engine_name == "Agent LLM":
                engine = AgentEngine(get_provider())
            else:
                engine = PynguinEngine()
            engines[engine_name] = engine
        except Exception as exc:
            engines[engine_name] = exc

    for function in functions:
        for engine_name in engine_names:
            engine = engines[engine_name]
            started = time.perf_counter()
            if isinstance(engine, Exception):
                results.append(
                    _failed_result(
                        function.name,
                        engine_name,
                        engine,
                        time.perf_counter() - started,
                    )
                )
                continue
            try:
                suite = engine.generate(function, source_path)
            except Exception as exc:
                results.append(
                    _failed_result(
                        function.name,
                        engine_name,
                        exc,
                        time.perf_counter() - started,
                    )
                )
                continue

            error_messages: list[str] = []
            line_percent: float | None = None
            branch_percent: float | None = None
            mutation_score: float | None = None
            wrong_test_count: int | None = None
            wrong_test_status: str | None = None
            surviving_mutant_names: tuple[str, ...] = ()
            mutant_explanations = ()
            flaky_test_names: tuple[str, ...] = ()
            flaky_run_count: int | None = None
            flaky_timed_out_runs: tuple[int, ...] = ()
            flaky_inconclusive_runs: tuple[int, ...] = ()

            try:
                correctness = wrong_test_detector.evaluate(
                    suite.test_code,
                    source_path,
                    is_benchmark=False,
                )
                wrong_test_status = correctness.status
                wrong_test_count = correctness.failing_tests
            except Exception as exc:
                correctness = None
                error_messages.append(f"Wrong-test check: {_format_error(exc)}")

            selection = None
            if correctness is not None:
                selection = passing_test_selection(
                    suite.test_code,
                    correctness.sandbox_result.test_outcomes,
                )
                if selection is not None:
                    coverage_deselected = selection.for_test_file(
                        "tests/test_generated.py"
                    )
                    mutation_deselected = coverage_deselected
                    has_passing_tests = selection.passing_test_count > 0
                else:
                    coverage_deselected = ()
                    mutation_deselected = ()
                    has_passing_tests = False
            else:
                coverage_deselected = ()
                mutation_deselected = ()
                has_passing_tests = False
            if has_passing_tests:
                try:
                    coverage = coverage_evaluator.evaluate(
                        suite.test_code,
                        source_path,
                        coverage_deselected,
                    )
                    line_percent = coverage.line_percent
                    branch_percent = coverage.branch_percent
                except Exception as exc:
                    error_messages.append(f"Coverage: {_format_error(exc)}")
                try:
                    mutation = mutation_evaluator.evaluate(
                        suite.test_code,
                        source_path,
                        mutation_deselected,
                    )
                    mutation_score = mutation.mutation_score
                    surviving_mutant_names = mutation.surviving_mutant_names
                    mutant_explanations = explain_mutants(
                        mutation.surviving_mutant_diffs
                    )
                except Exception as exc:
                    error_messages.append(f"Mutation: {_format_error(exc)}")

            try:
                flaky_result = flaky_test_checker.evaluate(
                    suite.test_code,
                    source_path,
                )
                flaky_test_names = flaky_result.flaky_test_names
                flaky_run_count = flaky_result.run_count
                flaky_timed_out_runs = flaky_result.timed_out_runs
                flaky_inconclusive_runs = flaky_result.inconclusive_runs
            except Exception as exc:
                error_messages.append(f"Flaky check: {_format_error(exc)}")

            results.append(
                EngineRun(
                    function_name=function.name,
                    engine_name=_ENGINE_KEYS[engine_name],
                    status="error" if error_messages else "completed",
                    error="; ".join(error_messages) or None,
                    line_percent=line_percent,
                    branch_percent=branch_percent,
                    mutation_score=mutation_score,
                    wrong_test_count=wrong_test_count,
                    wrong_test_status=wrong_test_status,
                    wall_clock_seconds=suite.wall_clock_seconds,
                    estimated_cost_usd=suite.estimated_cost_usd,
                    test_code=suite.test_code,
                    flaky_test_names=flaky_test_names,
                    flaky_run_count=flaky_run_count,
                    flaky_timed_out_runs=flaky_timed_out_runs,
                    flaky_inconclusive_runs=flaky_inconclusive_runs,
                    surviving_mutant_names=surviving_mutant_names,
                    mutant_explanations=mutant_explanations,
                )
            )

    for function in functions:
        generated_suites = {
            result.engine_name: result.test_code
            for result in results
            if result.function_name == function.name and result.test_code is not None
        }
        if not generated_suites:
            continue
        started = time.perf_counter()
        try:
            merge = BestOfMerger(
                mutation_evaluator=mutation_evaluator,
                wrong_test_detector=wrong_test_detector,
            ).merge(source_path, generated_suites)
            coverage = coverage_evaluator.evaluate(merge.test_code, source_path)
            flaky = flaky_test_checker.evaluate(merge.test_code, source_path)
            mutation = merge.mutation_result
            results.append(
                EngineRun(
                    function_name=function.name,
                    engine_name="best-of-merge",
                    status="completed",
                    line_percent=coverage.line_percent,
                    branch_percent=coverage.branch_percent,
                    mutation_score=mutation.mutation_score,
                    wrong_test_count=0,
                    wrong_test_status="passed",
                    wall_clock_seconds=time.perf_counter() - started,
                    estimated_cost_usd=0.0,
                    test_code=merge.test_code,
                    flaky_test_names=flaky.flaky_test_names,
                    flaky_run_count=flaky.run_count,
                    flaky_timed_out_runs=flaky.timed_out_runs,
                    flaky_inconclusive_runs=flaky.inconclusive_runs,
                    surviving_mutant_names=mutation.surviving_mutant_names,
                    mutant_explanations=explain_mutants(
                        mutation.surviving_mutant_diffs
                    ),
                    merge_selected_test_names=merge.selected_test_names,
                    merge_mutants_killed=merge.mutants_killed_by_selection,
                    merge_mutants_available=merge.mutants_available,
                )
            )
        except Exception as exc:
            results.append(
                EngineRun(
                    function_name=function.name,
                    engine_name="best-of-merge",
                    status="error",
                    error=_format_error(exc),
                    wall_clock_seconds=time.perf_counter() - started,
                )
            )
    return results


def _failed_result(
    function_name: str,
    engine_name: str,
    error: Exception,
    elapsed_seconds: float,
) -> EngineRun:
    """Create a visible result row for an engine failure."""
    return EngineRun(
        function_name=function_name,
        engine_name=_ENGINE_KEYS[engine_name],
        status="error",
        error=_format_error(error),
        wall_clock_seconds=elapsed_seconds,
    )


def _format_error(error: Exception) -> str:
    """Format an exception with its type for display and history."""
    message = str(error).strip() or "(no details)"
    return f"{type(error).__name__}: {message}"
