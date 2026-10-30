"""Summarize HumanEval experiment results and render report charts."""

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

_ENGINE_ORDER = ("single-shot-llm", "agent-llm", "pynguin")
_PAIRED_METRICS = (
    "line_percent",
    "branch_percent",
    "mutation_score",
    "wrong_test_count",
    "total_seconds",
    "estimated_cost_usd",
)
_FAILURE_CATEGORIES = (
    "timeout",
    "token-repeat",
    "no_scorable_tests",
    "infrastructure error",
)


@dataclass(frozen=True)
class EngineMetrics:
    """Hold means measured on the shared complete-case task set."""

    functions_included: int
    average_line_coverage: float
    average_branch_coverage: float
    average_mutation_score: float
    average_wrong_tests: float
    average_time_seconds: float
    average_cost_usd: float


@dataclass(frozen=True)
class PairwiseTest:
    """Hold one paired Wilcoxon signed-rank test result."""

    engine_a: str
    engine_b: str
    functions_included: int
    statistic: float | None
    p_value: float | None


@dataclass(frozen=True)
class HumanEvalAnalysis:
    """Contain complete-case, all-function, and paired-test summaries."""

    task_count: int
    paired_task_ids: tuple[str, ...]
    engine_metrics: Mapping[str, EngineMetrics]
    failure_counts: Mapping[str, Mapping[str, int]]
    pairwise_tests: tuple[PairwiseTest, ...]
    pynguin_xfail_only_count: int

    @property
    def paired_task_count(self) -> int:
        """Return the number of tasks in the complete-case cohort."""
        return len(self.paired_task_ids)


def analyze_rows(rows: Sequence[Mapping[str, str]]) -> HumanEvalAnalysis:
    """Calculate fair paired means, failure counts, and Wilcoxon tests."""
    if not rows:
        raise ValueError("The experiment CSV contains no result rows")

    by_task: dict[str, dict[str, Mapping[str, str]]] = {}
    for row in rows:
        task_id = row.get("task_id", "")
        engine = row.get("engine_name", "")
        if not task_id or engine not in _ENGINE_ORDER:
            raise ValueError(f"Invalid task or engine in experiment row: {task_id!r}, {engine!r}")
        task_engines = by_task.setdefault(task_id, {})
        if engine in task_engines:
            raise ValueError(f"Duplicate result for {task_id} and {engine}")
        task_engines[engine] = row

    for task_id, task_engines in by_task.items():
        missing = set(_ENGINE_ORDER) - task_engines.keys()
        if missing:
            raise ValueError(
                f"Task {task_id} is missing engine results: {', '.join(sorted(missing))}"
            )

    paired_task_ids = tuple(
        task_id
        for task_id, task_engines in by_task.items()
        if all(
            _number(task_engines[engine], metric) is not None
            for engine in _ENGINE_ORDER
            for metric in _PAIRED_METRICS
        )
    )
    engine_metrics = {
        engine: _engine_metrics(engine, by_task, paired_task_ids)
        for engine in _ENGINE_ORDER
    }
    pairwise_tests = tuple(
        _paired_wilcoxon(engine_a, engine_b, by_task)
        for index, engine_a in enumerate(_ENGINE_ORDER)
        for engine_b in _ENGINE_ORDER[index + 1 :]
    )
    failure_counts = {
        engine: _failure_counts(
            [task_engines[engine] for task_engines in by_task.values()]
        )
        for engine in _ENGINE_ORDER
    }
    pynguin_xfail_only_count = 0
    for task_engines in by_task.values():
        pynguin = task_engines["pynguin"]
        expected = _number(pynguin, "expected_failure_count")
        passing = _number(pynguin, "passing_test_count")
        wrong = _number(pynguin, "wrong_test_count")
        pynguin_xfail_only_count += (
            expected is not None
            and expected > 0
            and passing == 0
            and wrong == 0
        )

    return HumanEvalAnalysis(
        task_count=len(by_task),
        paired_task_ids=paired_task_ids,
        engine_metrics=engine_metrics,
        failure_counts=failure_counts,
        pairwise_tests=pairwise_tests,
        pynguin_xfail_only_count=pynguin_xfail_only_count,
    )


def generate_report(input_csv: Path, output_dir: Path) -> Path:
    """Read an experiment CSV and write a Markdown report with PNG charts."""
    rows = _read_csv(input_csv)
    analysis = analyze_rows(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_paths = _render_charts(analysis, output_dir)
    report_path = output_dir / "summary.md"
    report_path.write_text(
        _render_markdown(analysis, rows, input_csv, chart_paths),
        encoding="utf-8",
    )
    return report_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read experiment rows and reject malformed CSV input."""
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_fields = {
            "task_id",
            "engine_name",
            *_PAIRED_METRICS,
            "error",
            "status",
            "no_scorable_tests",
            "expected_failure_count",
            "passing_test_count",
        }
        missing = required_fields - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}"
            )
        return list(reader)


def _number(
    row: Mapping[str, str],
    field: str,
    default: float | None = None,
) -> float | None:
    """Parse a finite numeric CSV cell, preserving blank values as missing."""
    value = row.get(field, "")
    if value == "":
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Non-finite numeric value for {field}: {value!r}")
    return number


def _engine_metrics(
    engine: str,
    by_task: Mapping[str, Mapping[str, Mapping[str, str]]],
    task_ids: Sequence[str],
) -> EngineMetrics:
    """Average each requested metric over one shared complete-case cohort."""
    values = {
        metric: [
            _number(by_task[task_id][engine], metric)
            for task_id in task_ids
        ]
        for metric in _PAIRED_METRICS
    }
    count = len(task_ids)

    def average(metric: str) -> float | None:
        if count == 0:
            return None
        return sum(value for value in values[metric] if value is not None) / count

    return EngineMetrics(
        functions_included=count,
        average_line_coverage=average("line_percent"),
        average_branch_coverage=average("branch_percent"),
        average_mutation_score=average("mutation_score"),
        average_wrong_tests=average("wrong_test_count"),
        average_time_seconds=average("total_seconds"),
        average_cost_usd=average("estimated_cost_usd"),
    )


def _paired_wilcoxon(
    engine_a: str,
    engine_b: str,
    by_task: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> PairwiseTest:
    """Test mutation scores on tasks with values for both engines."""
    task_ids = [
        task_id
        for task_id, task_engines in by_task.items()
        if _number(task_engines[engine_a], "mutation_score") is not None
        and _number(task_engines[engine_b], "mutation_score") is not None
    ]
    scores_a = [
        _number(by_task[task_id][engine_a], "mutation_score")
        for task_id in task_ids
    ]
    scores_b = [
        _number(by_task[task_id][engine_b], "mutation_score")
        for task_id in task_ids
    ]
    if not task_ids:
        return PairwiseTest(engine_a, engine_b, 0, None, None)
    if all(left == right for left, right in zip(scores_a, scores_b)):
        return PairwiseTest(engine_a, engine_b, len(task_ids), 0.0, 1.0)

    result = wilcoxon(
        scores_a,
        scores_b,
        alternative="two-sided",
        zero_method="wilcox",
        method="auto",
    )
    return PairwiseTest(
        engine_a,
        engine_b,
        len(task_ids),
        float(result.statistic),
        float(result.pvalue),
    )


def _failure_counts(
    rows: Sequence[Mapping[str, str]],
) -> dict[str, int]:
    """Count reported failure categories; categories may overlap."""
    counts = dict.fromkeys(_FAILURE_CATEGORIES, 0)
    for row in rows:
        error = row.get("error", "").lower()
        counts["timeout"] += "timeout" in error or "timed out" in error
        counts["token-repeat"] += "token repeat limit reached" in error
        counts["no_scorable_tests"] += row.get("no_scorable_tests", "").lower() == "true"
        counts["infrastructure error"] += (
            row.get("status", "").lower() == "infrastructure_error"
        )
    return counts


def _render_charts(
    analysis: HumanEvalAnalysis,
    output_dir: Path,
) -> dict[str, Path]:
    """Render the paired-cohort metrics as publication-ready PNG charts."""
    names = [_display_engine(engine) for engine in _ENGINE_ORDER]
    metrics = analysis.engine_metrics
    charts = {
        "mutation": output_dir / "humaneval_mutation_score.png",
        "coverage": output_dir / "humaneval_coverage.png",
        "time": output_dir / "humaneval_average_time.png",
    }

    figure, axis = plt.subplots(figsize=(8, 5))
    values = [
        metrics[engine].average_mutation_score
        if metrics[engine].average_mutation_score is not None
        else math.nan
        for engine in _ENGINE_ORDER
    ]
    axis.bar(names, values, color=("#4472C4", "#70AD47", "#ED7D31"))
    axis.set_ylim(0, 1)
    axis.set_ylabel("Average mutation score")
    axis.set_title(f"Mutation score (paired n={analysis.paired_task_count})")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(charts["mutation"], dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 5))
    positions = range(len(_ENGINE_ORDER))
    width = 0.36
    line_values = [
        metrics[engine].average_line_coverage
        if metrics[engine].average_line_coverage is not None
        else math.nan
        for engine in _ENGINE_ORDER
    ]
    branch_values = [
        metrics[engine].average_branch_coverage
        if metrics[engine].average_branch_coverage is not None
        else math.nan
        for engine in _ENGINE_ORDER
    ]
    axis.bar(
        [position - width / 2 for position in positions],
        line_values,
        width,
        label="Line",
        color="#4472C4",
    )
    axis.bar(
        [position + width / 2 for position in positions],
        branch_values,
        width,
        label="Branch",
        color="#70AD47",
    )
    axis.set_xticks(list(positions), names)
    axis.set_ylim(0, 100)
    axis.set_ylabel("Average coverage (%)")
    axis.set_title(f"Coverage (paired n={analysis.paired_task_count})")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(charts["coverage"], dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 5))
    time_values = [
        metrics[engine].average_time_seconds
        if metrics[engine].average_time_seconds is not None
        else math.nan
        for engine in _ENGINE_ORDER
    ]
    axis.bar(names, time_values, color=("#4472C4", "#70AD47", "#ED7D31"))
    axis.set_ylabel("Average total time (seconds)")
    axis.set_title(f"Average time (paired n={analysis.paired_task_count})")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(charts["time"], dpi=160)
    plt.close(figure)
    return charts


def _render_markdown(
    analysis: HumanEvalAnalysis,
    rows: Sequence[Mapping[str, str]],
    input_csv: Path,
    charts: Mapping[str, Path],
) -> str:
    """Build the report text, including cohort and failure definitions."""
    metadata_row = rows[0]
    lines = [
        "# HumanEval Full Experiment Analysis",
        "",
        f"- Source: `{input_csv}`",
        f"- Run date: {metadata_row.get('run_date', 'not recorded')}",
        f"- LLM model: {metadata_row.get('model_name', 'not recorded')}",
        f"- Functions in CSV: {analysis.task_count}",
        "",
        "## Paired comparison",
        "",
        (
            "All engine averages below use the same complete-case functions: "
            "each of the three engines must have line coverage, branch coverage, "
            "mutation score, wrong-test count, total time, and estimated cost."
        ),
        "",
        (
            "| Engine | Functions included | Avg line coverage (%) | "
            "Avg branch coverage (%) | Avg mutation score | Avg wrong tests | "
            "Avg time (s) | Avg cost (USD) |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for engine in _ENGINE_ORDER:
        metric = analysis.engine_metrics[engine]
        lines.append(
            f"| {_display_engine(engine)} | {metric.functions_included} "
            f"| {_format_metric(metric.average_line_coverage, '.2f')} "
            f"| {_format_metric(metric.average_branch_coverage, '.2f')} "
            f"| {_format_metric(metric.average_mutation_score, '.4f')} "
            f"| {_format_metric(metric.average_wrong_tests, '.3f')} "
            f"| {_format_metric(metric.average_time_seconds, '.2f')} "
            f"| {_format_metric(metric.average_cost_usd, '.6f')} |"
        )

    lines.extend(
        [
            "",
            "## All-functions failure counts",
            "",
            (
                "Counts use all functions in the CSV for each engine. Categories "
                "are independent and can overlap; `no_scorable_tests` is a scoring "
                "state, not necessarily an infrastructure failure."
            ),
            "",
            (
                "| Engine | Functions | Timeout | Token-repeat | "
                "No scorable tests | Infrastructure error |"
            ),
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for engine in _ENGINE_ORDER:
        counts = analysis.failure_counts[engine]
        lines.append(
            f"| {_display_engine(engine)} | {analysis.task_count} "
            f"| {counts['timeout']} | {counts['token-repeat']} "
            f"| {counts['no_scorable_tests']} "
            f"| {counts['infrastructure error']} |"
        )

    lines.extend(
        [
            "",
            "## Paired Wilcoxon signed-rank tests",
            "",
            (
                "Two-sided tests compare mutation scores on every task with a "
                "score from both engines in that pair. The reported `n` is the "
                "number of paired tasks; p-values are unadjusted."
            ),
            "",
            "| Engine pair | Paired functions | Statistic | p-value |",
            "|---|---:|---:|---:|",
        ]
    )
    for result in analysis.pairwise_tests:
        statistic = (
            f"{result.statistic:.4f}" if result.statistic is not None else "n/a"
        )
        p_value = f"{result.p_value:.6g}" if result.p_value is not None else "n/a"
        lines.append(
            f"| {_display_engine(result.engine_a)} vs "
            f"{_display_engine(result.engine_b)} | {result.functions_included} "
            f"| {statistic} | {p_value} |"
        )

    lines.extend(
        [
            "",
            "## Pynguin xfail-only suites",
            "",
            (
                f"Pynguin produced **{analysis.pynguin_xfail_only_count}** suites "
                "with at least one xfail-marked test and no passing or wrong tests."
            ),
            "",
            "## Charts",
            "",
            f"![Mutation score by engine]({charts['mutation'].name})",
            "",
            f"![Line and branch coverage by engine]({charts['coverage'].name})",
            "",
            f"![Average time by engine]({charts['time'].name})",
            "",
        ]
    )
    return "\n".join(lines)


def _display_engine(engine: str) -> str:
    """Return a readable engine label for tables and charts."""
    return {
        "single-shot-llm": "Single-shot LLM",
        "agent-llm": "Agent LLM",
        "pynguin": "Pynguin",
    }[engine]


def _format_metric(value: float | None, format_spec: str) -> str:
    """Format an unavailable mean as n/a instead of implying a zero."""
    return format(value, format_spec) if value is not None else "n/a"


def main(argv: list[str] | None = None) -> int:
    """Generate the HumanEval Markdown summary and charts."""
    parser = argparse.ArgumentParser(prog="python -m testpilot.humaneval_analysis")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/v2/humaneval_full_164.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/v2"))
    arguments = parser.parse_args(argv)
    report = generate_report(arguments.input, arguments.output_dir)
    print(f"Wrote analysis report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
