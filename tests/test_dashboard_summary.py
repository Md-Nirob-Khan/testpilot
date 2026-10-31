"""Tests for the CSV-backed experiment dashboard summary."""

import csv
from pathlib import Path

from testpilot.dashboard_summary import load_experiment_dashboard_summary

_ENGINES = ("single-shot-llm", "agent-llm", "pynguin")
_METRICS = (
    "line_percent",
    "branch_percent",
    "mutation_score",
    "wrong_test_count",
    "total_seconds",
    "estimated_cost_usd",
)


def _row(task: int, engine: str) -> dict[str, str]:
    """Create one deterministic HumanEval-like result row."""
    offset = _ENGINES.index(engine)
    return {
        "task_id": f"HumanEval/{task}",
        "engine_name": engine,
        "line_percent": str(40 + task * 10 + offset),
        "branch_percent": str(30 + task * 10 + offset),
        "mutation_score": str(0.2 + task * 0.1 + offset * 0.05),
        "wrong_test_count": "0",
        "total_seconds": str(2 + task + offset),
        "estimated_cost_usd": "0.01",
        "error": "",
        "rescore_error": "",
        "status": "completed",
        "does_not_call_target": "False",
        "no_scorable_tests": "False",
        "passing_test_count": "1",
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows using a consistent CSV schema."""
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def test_summary_calculates_paired_results_and_all_failure_counts(
    tmp_path: Path,
) -> None:
    """Use the CSV for headline values, error counts, and target-call callout."""
    rows = [
        _row(task, engine)
        for task in range(3)
        for engine in _ENGINES
    ]
    rows[0].update(
        does_not_call_target="True",
        passing_test_count="2",
    )
    rows[3].update(
        does_not_call_target="True",
        passing_test_count="0",
        wrong_test_count="1",
        no_scorable_tests="True",
        error="generation request timed out",
    )
    rows[5].update(
        does_not_call_target="True",
        no_scorable_tests="True",
        error="Mutation: mutmut could not produce a score",
        rescore_error="RuntimeError: mutation metadata missing",
    )
    rows[7].update(wrong_test_count="2")
    for engine in _ENGINES:
        failure_row = _row(3, engine)
        for metric in _METRICS:
            failure_row[metric] = ""
        if engine == "agent-llm":
            failure_row["error"] = "request timed out"
        rows.append(failure_row)

    csv_path = tmp_path / "experiment.csv"
    _write_rows(csv_path, rows)

    summary = load_experiment_dashboard_summary(csv_path)

    assert summary.task_count == 4
    assert summary.paired_function_count == 3
    assert summary.single_shot_passed_without_target == 1
    single_shot, agent, pynguin = summary.engines
    assert single_shot.line_coverage == 50
    assert single_shot.timeout_rows == 1
    assert single_shot.does_not_call_target_rows == 2
    assert agent.timeout_rows == 1
    assert agent.wrong_test_cases == 2
    assert pynguin.no_scorable_tests_rows == 1
    assert pynguin.does_not_call_target_rows == 1
    assert pynguin.mutation_error_rows == 1
    assert len(summary.wilcoxon_tests) == 3
    assert all(
        result.p_value is not None and 0 <= result.p_value <= 1
        for result in summary.wilcoxon_tests
    )


def test_summary_rejects_an_empty_csv(tmp_path: Path) -> None:
    """Report a clear error instead of showing success-shaped empty metrics."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("task_id,engine_name\n", encoding="utf-8")

    try:
        load_experiment_dashboard_summary(csv_path)
    except ValueError as exc:
        assert "no result rows" in str(exc)
    else:
        raise AssertionError("Expected an empty experiment CSV to be rejected")
