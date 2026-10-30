"""Generate and evaluate selected engines for dashboard comparisons."""

import time
from pathlib import Path
from typing import Callable, Mapping, Sequence

from testpilot.analyzer import FunctionInfo
from testpilot.engines import AgentEngine, PynguinEngine, SingleShotEngine
from testpilot.engines.base import TestGenerationEngine
from testpilot.evaluator import (
    CoverageEvaluator,
    MutationEvaluator,
    WrongTestDetector,
)
from testpilot.llm import LLMProvider, create_provider
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

            try:
                coverage = coverage_evaluator.evaluate(suite.test_code, source_path)
                line_percent = coverage.line_percent
                branch_percent = coverage.branch_percent
            except Exception as exc:
                error_messages.append(f"Coverage: {_format_error(exc)}")

            if correctness is not None and correctness.status == "passed":
                try:
                    mutation = mutation_evaluator.evaluate(
                        suite.test_code,
                        source_path,
                    )
                    mutation_score = mutation.mutation_score
                except Exception as exc:
                    error_messages.append(f"Mutation: {_format_error(exc)}")

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
                    wall_clock_seconds=time.perf_counter() - started,
                    estimated_cost_usd=suite.estimated_cost_usd,
                    test_code=suite.test_code,
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
