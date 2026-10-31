"""Load CSV-derived metrics for the Streamlit experiment-results page."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from testpilot.humaneval_analysis import EngineMetrics


@dataclass(frozen=True)
class ExperimentEngineSummary:
    """Contain paired metrics and all-row failure counts for one engine."""

    engine_name: str
    paired_functions: int
    line_coverage: float | None
    branch_coverage: float | None
    mutation_score: float | None
    average_wrong_tests: float | None
    average_time_seconds: float | None
    average_cost_usd: float | None
    timeout_rows: int
    wrong_test_cases: int
    does_not_call_target_rows: int
    no_scorable_tests_rows: int
    mutation_error_rows: int


@dataclass(frozen=True)
class WilcoxonSummary:
    """Contain one pairwise mutation-score test."""

    engine_a: str
    engine_b: str
    functions_included: int
    p_value: float | None


@dataclass(frozen=True)
class ExperimentDashboardSummary:
    """Contain the data-backed values displayed on the experiment page."""

    task_count: int
    paired_function_count: int
    engines: tuple[ExperimentEngineSummary, ...]
    wilcoxon_tests: tuple[WilcoxonSummary, ...]
    single_shot_passed_without_target: int


def load_experiment_dashboard_summary(
    csv_path: Path,
) -> ExperimentDashboardSummary:
    """Read experiment rows and calculate paired metrics and failure counts."""
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        raise ValueError(f"Experiment CSV contains no result rows: {path}")

    try:
        from testpilot.humaneval_analysis import analyze_rows
    except ImportError as exc:
        raise ImportError(
            "Experiment statistics require the optional analysis dependencies; "
            'install them with `python -m pip install -e ".[analysis]"`.'
        ) from exc

    analysis = analyze_rows(rows)
    engines = tuple(
        _engine_summary(engine_name, rows, analysis.engine_metrics[engine_name])
        for engine_name in analysis.engine_metrics
    )
    single_shot_passed_without_target = sum(
        _is_true(row.get("does_not_call_target"))
        and _is_true(row.get("status") == "completed")
        and (_numeric(row.get("passing_test_count")) or 0) > 0
        and (_numeric(row.get("wrong_test_count")) or 0) == 0
        for row in rows
        if row.get("engine_name") == "single-shot-llm"
    )
    return ExperimentDashboardSummary(
        task_count=analysis.task_count,
        paired_function_count=analysis.paired_task_count,
        engines=engines,
        wilcoxon_tests=tuple(
            WilcoxonSummary(
                engine_a=test.engine_a,
                engine_b=test.engine_b,
                functions_included=test.functions_included,
                p_value=test.p_value,
            )
            for test in analysis.pairwise_tests
        ),
        single_shot_passed_without_target=single_shot_passed_without_target,
    )


def _engine_summary(
    engine_name: str,
    rows: list[Mapping[str, str]],
    metrics: "EngineMetrics",
) -> ExperimentEngineSummary:
    """Combine the paired analysis metrics with all-row counts."""
    engine_rows = [row for row in rows if row.get("engine_name") == engine_name]
    return ExperimentEngineSummary(
        engine_name=engine_name,
        paired_functions=metrics.functions_included,
        line_coverage=metrics.average_line_coverage,
        branch_coverage=metrics.average_branch_coverage,
        mutation_score=metrics.average_mutation_score,
        average_wrong_tests=metrics.average_wrong_tests,
        average_time_seconds=metrics.average_time_seconds,
        average_cost_usd=metrics.average_cost_usd,
        timeout_rows=sum(_is_timeout(row.get("error")) for row in engine_rows),
        wrong_test_cases=sum(
            _numeric(row.get("wrong_test_count")) or 0 for row in engine_rows
        ),
        does_not_call_target_rows=sum(
            _is_true(row.get("does_not_call_target")) for row in engine_rows
        ),
        no_scorable_tests_rows=sum(
            _is_true(row.get("no_scorable_tests")) for row in engine_rows
        ),
        mutation_error_rows=sum(_has_mutation_error(row) for row in engine_rows),
    )


def _is_timeout(error: str | None) -> bool:
    """Return whether an error message reports a timeout."""
    message = (error or "").lower()
    return "timeout" in message or "timed out" in message


def _has_mutation_error(row: Mapping[str, str]) -> bool:
    """Return whether a result row records a mutation-evaluation error."""
    return any(
        "mutation" in (row.get(field) or "").lower()
        for field in ("error", "rescore_error")
    )


def _is_true(value: str | bool | None) -> bool:
    """Interpret common CSV boolean representations."""
    return str(value).strip().lower() in {"true", "1", "yes"}


def _numeric(value: str | None) -> float | None:
    """Parse a finite numeric CSV cell, treating an empty cell as unavailable."""
    if value is None or not value.strip():
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Expected a numeric CSV value, got {value!r}") from exc
