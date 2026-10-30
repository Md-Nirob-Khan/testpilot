"""Run generation engines on HumanEval and export results to CSV."""

import argparse
import csv
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Sequence

from testpilot.analyzer import FunctionInfo, analyze_file
from testpilot.benchmarks import HumanEvalProblem, load_humaneval
from testpilot.engines import AgentEngine, PynguinEngine, SingleShotEngine
from testpilot.engines.base import GeneratedSuite, TestGenerationEngine
from testpilot.evaluator import (
    CoverageEvaluator,
    MutationEvaluator,
    WrongTestDetector,
)
from testpilot.llm import LLMProvider, LLMProviderError, create_provider
from testpilot.sandbox import passing_test_selection

_CSV_FIELDS = (
    "run_date",
    "run_started_at",
    "dataset",
    "task_id",
    "function_name",
    "engine_name",
    "model_name",
    "temperature",
    "seed",
    "engine_settings",
    "status",
    "error",
    "generation_seconds",
    "total_seconds",
    "llm_tokens_used",
    "estimated_cost_usd",
    "rounds",
    "line_percent",
    "branch_percent",
    "mutation_score",
    "total_mutants",
    "killed_mutants",
    "survived_mutants",
    "wrong_test_count",
    "passing_test_count",
    "expected_failure_count",
    "no_scorable_tests",
    "wrong_test_status",
    "wrong_test_reasons_json",
)


@dataclass(frozen=True)
class ExperimentRow:
    """Hold exported measurements for one function-engine combination."""

    run_date: str
    run_started_at: str
    dataset: str
    task_id: str
    function_name: str
    engine_name: str
    model_name: str
    temperature: float | None
    seed: int | None
    engine_settings: str
    status: str
    error: str
    generation_seconds: float | None
    total_seconds: float
    llm_tokens_used: int | None
    estimated_cost_usd: float | None
    rounds: int | None
    line_percent: float | None
    branch_percent: float | None
    mutation_score: float | None
    total_mutants: int | None
    killed_mutants: int | None
    survived_mutants: int | None
    wrong_test_count: int | None
    passing_test_count: int | None
    expected_failure_count: int | None
    no_scorable_tests: bool
    wrong_test_status: str
    wrong_test_reasons_json: str


@dataclass(frozen=True)
class ExperimentSummary:
    """Summarize the trial measurements and output location."""

    rows: tuple[ExperimentRow, ...]
    output_path: Path
    run_date: str
    model_name: str
    elapsed_seconds: float


def run_humaneval_experiment(
    dataset_path: Path,
    output_path: Path,
    limit: int = 10,
    offset: int = 0,
    task_ids: Sequence[str] | None = None,
    resume: bool = False,
) -> ExperimentSummary:
    """Run all three engines on a HumanEval slice and write a CSV report."""
    started = time.perf_counter()
    started_at = datetime.now().astimezone()
    run_date = started_at.date().isoformat()
    run_started_at = started_at.isoformat(timespec="seconds")
    if task_ids is None:
        problems = load_humaneval(
            dataset_path,
            limit=limit,
            offset=offset,
        )
    else:
        if not task_ids or len(set(task_ids)) != len(task_ids):
            raise ValueError("task_ids must be a non-empty sequence without duplicates")
        if offset:
            raise ValueError("task_ids cannot be combined with a non-zero offset")
        available = {
            problem.task_id: problem
            for problem in load_humaneval(dataset_path)
        }
        missing = [task_id for task_id in task_ids if task_id not in available]
        if missing:
            raise ValueError(f"Unknown HumanEval task IDs: {', '.join(missing)}")
        problems = tuple(available[task_id] for task_id in task_ids)
    provider = create_provider()
    model_name = _model_name(provider)
    temperature, seed = _sampling_settings(provider)
    engine_specs = _engine_specs(provider)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    recorded_engines: dict[str, set[str]] = {}
    if resume and output.exists():
        with output.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            if tuple(reader.fieldnames or ()) != _CSV_FIELDS:
                raise ValueError(
                    f"Cannot resume from {output}: CSV headers do not match"
                )
            for existing_row in reader:
                task_id = existing_row.get("task_id")
                engine_name = existing_row.get("engine_name")
                if task_id and engine_name:
                    recorded_engines.setdefault(task_id, set()).add(engine_name)

    rows: list[ExperimentRow] = []
    append = resume and output.exists()
    with output.open("a" if append else "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=_CSV_FIELDS,
            lineterminator="\n",
        )
        if not append:
            writer.writeheader()
            csv_file.flush()
        for problem in problems:
            with TemporaryDirectory(prefix="testpilot-humaneval-") as directory:
                source_path = Path(directory) / "testpilot_target.py"
                source_path.write_text(problem.source_code, encoding="utf-8")
                function = _find_function(problem, source_path)
                for engine_name, engine_settings, engine_factory in engine_specs:
                    if engine_name in recorded_engines.get(problem.task_id, set()):
                        continue
                    row = _run_one(
                        problem=problem,
                        function=function,
                        source_path=source_path,
                        engine_name=engine_name,
                        engine_settings=engine_settings,
                        engine=engine_factory(),
                        model_name=model_name,
                        temperature=(
                            temperature if engine_name != "pynguin" else None
                        ),
                        seed=seed if engine_name != "pynguin" else None,
                        run_date=run_date,
                        run_started_at=run_started_at,
                    )
                    rows.append(row)
                    writer.writerow(asdict(row))
                    csv_file.flush()
                    recorded_engines.setdefault(problem.task_id, set()).add(
                        engine_name
                    )

    return ExperimentSummary(
        rows=tuple(rows),
        output_path=output,
        run_date=run_date,
        model_name=model_name,
        elapsed_seconds=time.perf_counter() - started,
    )


def _engine_specs(
    provider: LLMProvider,
) -> tuple[tuple[str, str, Callable[[], TestGenerationEngine]], ...]:
    """Build the engines with explicit, recorded trial settings."""
    return (
        (
            "single-shot-llm",
            "one generation attempt",
            lambda: SingleShotEngine(provider),
        ),
        (
            "agent-llm",
            "max_rounds=3; benchmark_mode=true",
            lambda: AgentEngine(provider, max_rounds=3, is_benchmark=True),
        ),
        (
            "pynguin",
            "search_time_seconds=30; timeout_seconds=120; seed=42",
            PynguinEngine,
        ),
    )


def _run_one(
    problem: HumanEvalProblem,
    function: FunctionInfo,
    source_path: Path,
    engine_name: str,
    engine_settings: str,
    engine: TestGenerationEngine,
    model_name: str,
    run_date: str,
    run_started_at: str,
    temperature: float | None = None,
    seed: int | None = None,
) -> ExperimentRow:
    """Generate and evaluate one engine's tests against a canonical solution."""
    started = time.perf_counter()
    suite: GeneratedSuite | None = None
    errors: list[str] = []
    line_percent = None
    branch_percent = None
    mutation_score = None
    total_mutants = None
    killed_mutants = None
    survived_mutants = None
    wrong_test_count = None
    passing_test_count = None
    expected_failure_count = 0
    no_scorable_tests = False
    wrong_test_status = ""
    wrong_test_reasons: list[dict[str, str]] = []
    infrastructure_error = False
    selection = None
    try:
        suite = engine.generate(function, source_path)
    except Exception as exc:
        errors.append(f"generation: {_format_error(exc)}")
        infrastructure_error = _is_ollama_connection_refused(exc)

    if suite is not None:
        try:
            correctness = WrongTestDetector(timeout_seconds=30.0).evaluate(
                suite.test_code,
                source_path,
                is_benchmark=True,
            )
            wrong_test_status = correctness.status
            selection = passing_test_selection(
                suite.test_code,
                correctness.sandbox_result.test_outcomes,
            )
            wrong_test_count = (
                selection.wrong_test_count
                if selection is not None
                else correctness.failing_tests
            )
            expected_failure_count = (
                selection.expected_failure_count
                if selection is not None
                else correctness.expected_failure_count
            )
            wrong_test_reasons = [
                {
                    "test_name": outcome.name,
                    "reason": outcome.failure_kind or "test_error",
                }
                for outcome in (
                    selection.wrong_test_outcomes if selection is not None else ()
                )
            ]
        except Exception as exc:
            correctness = None
            errors.append(f"wrong-test check: {_format_error(exc)}")

        if correctness is not None and selection is not None:
            if selection.passing_test_count > 0:
                passing_test_count = selection.passing_test_count
                coverage_deselected = selection.for_test_file(
                    "tests/test_generated.py"
                )
                mutation_deselected = coverage_deselected
            else:
                passing_test_count = 0
                no_scorable_tests = True
                coverage_deselected = ()
                mutation_deselected = ()
        elif correctness is not None:
            passing_test_count = 0
            no_scorable_tests = True
            coverage_deselected = ()
            mutation_deselected = ()
        else:
            passing_test_count = None
            coverage_deselected = ()
            mutation_deselected = ()
        if passing_test_count:
            try:
                coverage = CoverageEvaluator(timeout_seconds=30.0).evaluate(
                    suite.test_code,
                    source_path,
                    coverage_deselected,
                )
                line_percent = coverage.line_percent
                branch_percent = coverage.branch_percent
            except Exception as exc:
                if "no data to report" in str(exc).lower():
                    no_scorable_tests = True
                    line_percent = 0.0
                    branch_percent = 0.0
                    mutation_score = 0.0
                else:
                    errors.append(f"coverage: {_format_error(exc)}")
            if not no_scorable_tests:
                try:
                    mutation = MutationEvaluator(timeout_seconds=300.0).evaluate(
                        suite.test_code,
                        source_path,
                        mutation_deselected,
                    )
                    mutation_score = mutation.mutation_score
                    total_mutants = mutation.total_mutants
                    killed_mutants = mutation.killed_mutants
                    survived_mutants = mutation.survived_mutants
                except Exception as exc:
                    errors.append(f"mutation: {_format_error(exc)}")
        elif correctness is not None:
            line_percent = 0.0
            branch_percent = 0.0
            mutation_score = 0.0

    return ExperimentRow(
        run_date=run_date,
        run_started_at=run_started_at,
        dataset="openai/human-eval",
        task_id=problem.task_id,
        function_name=problem.entry_point,
        engine_name=engine_name,
        model_name=model_name,
        temperature=temperature,
        seed=seed,
        engine_settings=engine_settings,
        status=(
            "infrastructure_error"
            if infrastructure_error
            else "error"
            if errors
            else "completed"
        ),
        error="; ".join(errors),
        generation_seconds=(suite.wall_clock_seconds if suite else None),
        total_seconds=time.perf_counter() - started,
        llm_tokens_used=(suite.llm_tokens_used if suite else None),
        estimated_cost_usd=(suite.estimated_cost_usd if suite else None),
        rounds=(suite.rounds if suite else None),
        line_percent=line_percent,
        branch_percent=branch_percent,
        mutation_score=mutation_score,
        total_mutants=total_mutants,
        killed_mutants=killed_mutants,
        survived_mutants=survived_mutants,
        wrong_test_count=wrong_test_count,
        passing_test_count=passing_test_count,
        expected_failure_count=expected_failure_count,
        no_scorable_tests=no_scorable_tests,
        wrong_test_status=wrong_test_status,
        wrong_test_reasons_json=json.dumps(wrong_test_reasons, sort_keys=True),
    )


def _find_function(
    problem: HumanEvalProblem,
    source_path: Path,
) -> FunctionInfo:
    """Find the analyzed entry point for one canonical HumanEval problem."""
    functions = analyze_file(source_path)
    for function in functions:
        if function.name == problem.entry_point:
            return function
    raise ValueError(
        f"HumanEval entry point {problem.entry_point!r} was not analyzed"
    )


def _model_name(provider: LLMProvider) -> str:
    """Return the configured model identifier without exposing credentials."""
    model = getattr(provider, "model", None)
    if not isinstance(model, str) or not model:
        raise ValueError("The configured LLM provider has no model identifier")
    return model


def _sampling_settings(
    provider: LLMProvider,
) -> tuple[float | None, int | None]:
    """Return recorded sampling settings when the provider exposes them."""
    temperature = getattr(provider, "temperature", None)
    seed = getattr(provider, "seed", None)
    if temperature is not None and (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
    ):
        raise ValueError("The configured LLM provider has an invalid temperature")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
        raise ValueError("The configured LLM provider has an invalid seed")
    return (
        float(temperature) if temperature is not None else None,
        seed,
    )


def _format_error(error: Exception) -> str:
    """Format an exception for the CSV report."""
    message = " ".join(str(error).split()) or "(no details)"
    if len(message) > 500:
        message = f"{message[:497]}..."
    return f"{type(error).__name__}: {message}"


def _is_ollama_connection_refused(error: Exception) -> bool:
    """Identify a final Ollama connection refusal as an infrastructure failure."""
    return (
        isinstance(error, LLMProviderError)
        and "connection refused" in str(error).lower()
        and "ollama" in str(error).lower()
    )


def main(argv: list[str] | None = None) -> int:
    """Run a bounded HumanEval experiment from the command line."""
    parser = argparse.ArgumentParser(prog="python -m testpilot.experiment")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--task-ids", nargs="+")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="append to an existing CSV and skip recorded task/engine results",
    )
    arguments = parser.parse_args(argv)
    if arguments.limit < 1:
        parser.error("--limit must be positive")
    if arguments.offset < 0:
        parser.error("--offset cannot be negative")

    summary = run_humaneval_experiment(
        arguments.dataset,
        arguments.output,
        limit=arguments.limit,
        offset=arguments.offset,
        task_ids=arguments.task_ids,
        resume=arguments.resume,
    )
    completed = sum(row.status == "completed" for row in summary.rows)
    print(
        f"Saved {len(summary.rows)} engine results ({completed} completed) "
        f"to {summary.output_path}; model={summary.model_name}; "
        f"date={summary.run_date}; elapsed={summary.elapsed_seconds:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
