"""Tests for persisted dashboard comparison history."""

from pathlib import Path

import pytest

from testpilot.storage import EngineRun, RunHistory
from testpilot.evaluator import MutantExplanation


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
            flaky_test_names=("test_is_even::test_unstable",),
            flaky_run_count=3,
            surviving_mutant_names=("testpilot_target.mutant_3",),
            mutant_explanations=(
                MutantExplanation(
                    mutant_name="testpilot_target.mutant_3",
                    description="The comparison changes at its boundary.",
                    missing_test_case="Test equal operands.",
                    diff="- if value > 0\n+ if value >= 0",
                ),
            ),
            merge_selected_test_names=("pynguin:test_is_even",),
            merge_mutants_killed=3,
            merge_mutants_available=4,
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


def test_run_history_migrates_existing_engine_runs_table(tmp_path: Path) -> None:
    import sqlite3

    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_name TEXT NOT NULL,
                function_names_json TEXT NOT NULL
            );
            CREATE TABLE engine_runs (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(run_id),
                function_name TEXT NOT NULL,
                engine_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                line_percent REAL,
                branch_percent REAL,
                mutation_score REAL,
                wrong_test_count INTEGER,
                wrong_test_status TEXT,
                wall_clock_seconds REAL,
                estimated_cost_usd REAL,
                test_code TEXT
            );
            """
        )

    history = RunHistory(database_path)
    run_id = history.save_run(
        "old.py",
        ["answer"],
        [
            EngineRun(
                function_name="answer",
                engine_name="pynguin",
                status="completed",
                flaky_run_count=3,
            )
        ],
    )

    result = history.get_run(run_id).results[0]
    assert result.flaky_test_names == ()
    assert result.flaky_run_count == 3
    assert result.mutant_explanations == ()


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
