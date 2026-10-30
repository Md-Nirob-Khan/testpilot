"""Tests for HumanEval experiment analysis and report generation."""

import csv
from pathlib import Path

import pytest

from testpilot.humaneval_analysis import analyze_rows, generate_report

_ENGINES = ("single-shot-llm", "agent-llm", "pynguin")


def _row(task: int, engine: str) -> dict[str, str]:
    """Build a valid synthetic experiment row with deterministic metrics."""
    offset = _ENGINES.index(engine)
    return {
        "task_id": f"HumanEval/{task}",
        "engine_name": engine,
        "line_percent": str(50 + task * 10 + offset),
        "branch_percent": str(40 + task * 10 + offset),
        "mutation_score": str(0.2 + task * 0.2 + offset * 0.1),
        "wrong_test_count": str(task),
        "total_seconds": str(2 + task * 2 + offset),
        "estimated_cost_usd": str(task * 0.01),
        "error": "",
        "status": "completed",
        "no_scorable_tests": "False",
        "expected_failure_count": "0",
        "passing_test_count": "1",
    }


def _rows() -> list[dict[str, str]]:
    """Create three complete tasks and one task with engine failures."""
    rows = [_row(task, engine) for task in range(3) for engine in _ENGINES]
    pynguin_xfail = rows[8]
    pynguin_xfail.update(
        line_percent="0",
        branch_percent="0",
        mutation_score="0",
        wrong_test_count="0",
        no_scorable_tests="True",
        expected_failure_count="2",
        passing_test_count="0",
    )
    single_timeout = _row(3, "single-shot-llm")
    single_timeout.update(
        status="error",
        error="generation: TimeoutError: request timed out",
        line_percent="",
        branch_percent="",
        mutation_score="",
        wrong_test_count="",
        estimated_cost_usd="",
    )
    agent_repeat = _row(3, "agent-llm")
    agent_repeat.update(
        status="error",
        error="prediction aborted, token repeat limit reached",
        no_scorable_tests="True",
        line_percent="",
        branch_percent="",
        mutation_score="",
        wrong_test_count="",
        estimated_cost_usd="",
    )
    pynguin_error = _row(3, "pynguin")
    pynguin_error.update(
        status="infrastructure_error",
        error="Pynguin infrastructure failure",
        line_percent="",
        branch_percent="",
        mutation_score="",
        wrong_test_count="0",
        estimated_cost_usd="",
    )
    return [*rows, single_timeout, agent_repeat, pynguin_error]


def test_analysis_uses_shared_complete_cases_and_counts_all_failures() -> None:
    analysis = analyze_rows(_rows())

    assert analysis.task_count == 4
    assert analysis.paired_task_ids == (
        "HumanEval/0",
        "HumanEval/1",
        "HumanEval/2",
    )
    assert analysis.engine_metrics["single-shot-llm"].functions_included == 3
    assert analysis.engine_metrics["single-shot-llm"].average_line_coverage == 60
    assert analysis.engine_metrics["single-shot-llm"].average_mutation_score == pytest.approx(
        0.4
    )
    assert analysis.engine_metrics["single-shot-llm"].average_time_seconds == 4
    assert analysis.failure_counts["single-shot-llm"]["timeout"] == 1
    assert analysis.failure_counts["agent-llm"]["token-repeat"] == 1
    assert analysis.failure_counts["agent-llm"]["no_scorable_tests"] == 1
    assert analysis.failure_counts["pynguin"]["no_scorable_tests"] == 1
    assert analysis.failure_counts["pynguin"]["infrastructure error"] == 1
    assert analysis.pynguin_xfail_only_count == 1
    assert [test.functions_included for test in analysis.pairwise_tests] == [3, 3, 3]
    assert analysis.pairwise_tests[0].statistic == 0
    assert analysis.pairwise_tests[0].p_value == pytest.approx(0.25)
    assert all(
        test.p_value is not None and 0 <= test.p_value <= 1
        for test in analysis.pairwise_tests
    )


def test_analysis_keeps_empty_complete_case_means_unavailable() -> None:
    rows = [_row(0, engine) for engine in _ENGINES]
    for row in rows:
        row["mutation_score"] = ""

    analysis = analyze_rows(rows)

    assert analysis.paired_task_ids == ()
    assert all(
        metrics.average_mutation_score is None
        for metrics in analysis.engine_metrics.values()
    )


def test_analysis_rejects_duplicate_engine_results() -> None:
    rows = _rows()
    rows.append(_row(0, "single-shot-llm"))

    with pytest.raises(ValueError, match="Duplicate result"):
        analyze_rows(rows)


def test_report_writes_summary_and_three_png_charts(tmp_path: Path) -> None:
    input_path = tmp_path / "experiment.csv"
    rows = _rows()
    with input_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    report_path = generate_report(input_path, tmp_path / "report")

    report = report_path.read_text(encoding="utf-8")
    assert "Functions included" in report
    assert "Paired Wilcoxon signed-rank tests" in report
    assert "Pynguin produced **1** suites" in report
    for filename in (
        "humaneval_mutation_score.png",
        "humaneval_coverage.png",
        "humaneval_average_time.png",
    ):
        chart = report_path.parent / filename
        assert chart.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
