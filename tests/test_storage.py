"""Tests for persisted dashboard comparison history."""

from pathlib import Path

import pytest

from testpilot.storage import EngineRun, RunHistory


def test_run_history_round_trips_metrics_and_generated_code(tmp_path: Path) -> None:
    history = RunHistory(tmp_path / "nested" / "runs.sqlite3")
    results = [
        EngineRun(
            function_name="is_even",
            engine_name="pynguin",
            status="completed",
            line_percent=100.0,
            branch_percent=50.0,
            mutation_score=0.75,
            wrong_test_count=0,
            wrong_test_status="passed",
            wall_clock_seconds=2.5,
            estimated_cost_usd=0.0,
            test_code="def test_is_even():\n    assert True\n",
        ),
        EngineRun(
            function_name="is_even",
            engine_name="agent-llm",
            status="error",
            error="LLMProviderError: request unavailable",
        ),
    ]

    run_id = history.save_run("sample.py", ["is_even"], results)

    assert history.list_runs() == [
        history.get_run(run_id).summary,
    ]
    run = history.get_run(run_id)
    assert run.summary.source_name == "sample.py"
    assert run.summary.function_names == ("is_even",)
    assert run.results == tuple(results)


def test_run_history_keeps_empty_runs_and_rejects_unknown_run(
    tmp_path: Path,
) -> None:
    history = RunHistory(tmp_path / "runs.sqlite3")
    run_id = history.save_run("broken.py", [], [])

    assert history.get_run(run_id).results == ()
    with pytest.raises(KeyError, match="Run 999 does not exist"):
        history.get_run(999)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_run_history_rejects_invalid_limit(tmp_path: Path, limit: int) -> None:
    history = RunHistory(tmp_path / "runs.sqlite3")

    with pytest.raises(ValueError, match="History limit must be a positive integer"):
        history.list_runs(limit=limit)
