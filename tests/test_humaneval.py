"""Tests for HumanEval loading and experiment CSV reporting."""

import csv
import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from testpilot.engines.base import GeneratedSuite
from testpilot.experiment import _format_error, run_humaneval_experiment
from testpilot.evaluator import MutationResult
from testpilot.benchmarks import load_humaneval


def _record() -> dict[str, str]:
    return {
        "task_id": "HumanEval/0",
        "entry_point": "add",
        "prompt": "def add(left, right):\n",
        "canonical_solution": "    return left + right\n",
    }


def test_load_humaneval_reads_gzip_and_limits_records(tmp_path: Path) -> None:
    dataset_path = tmp_path / "HumanEval.jsonl.gz"
    records = [_record(), {**_record(), "task_id": "HumanEval/1"}]
    with gzip.open(dataset_path, "wt", encoding="utf-8") as dataset:
        dataset.write("\n".join(json.dumps(record) for record in records))

    problems = load_humaneval(dataset_path, limit=1)

    assert len(problems) == 1
    assert problems[0].task_id == "HumanEval/0"
    assert problems[0].source_code == (
        "def add(left, right):\n    return left + right\n"
    )


@pytest.mark.parametrize("record", [{}, {"task_id": "HumanEval/0"}])
def test_load_humaneval_rejects_incomplete_records(
    tmp_path: Path,
    record: dict[str, str],
) -> None:
    dataset_path = tmp_path / "HumanEval.jsonl"
    dataset_path.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required string fields"):
        load_humaneval(dataset_path)


def test_error_formatting_is_single_line_and_bounded() -> None:
    assert _format_error(RuntimeError("first line\n second line")) == (
        "RuntimeError: first line second line"
    )
    assert len(_format_error(RuntimeError("x" * 600))) == 514


def test_trial_writes_three_benchmark_engine_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.experiment as experiment

    dataset_path = tmp_path / "HumanEval.jsonl"
    dataset_path.write_text(json.dumps(_record()), encoding="utf-8")
    events: list[bool] = []

    class FakeEngine:
        def generate(self, function_info, source_path):
            return GeneratedSuite(
                test_code="def test_add():\n    assert True\n",
                engine_name="fake",
                wall_clock_seconds=0.25,
                llm_tokens_used=12,
                estimated_cost_usd=0.01,
            )

    class FakeWrongTestDetector:
        def __init__(self, timeout_seconds):
            assert timeout_seconds == 30.0

        def evaluate(self, test_code, source_path, is_benchmark):
            events.append(is_benchmark)
            return SimpleNamespace(status="passed", failing_tests=0)

    class FakeCoverageEvaluator:
        def __init__(self, timeout_seconds):
            assert timeout_seconds == 30.0

        def evaluate(self, test_code, source_path):
            return SimpleNamespace(line_percent=75.0, branch_percent=50.0)

    class FakeMutationEvaluator:
        def __init__(self, timeout_seconds):
            assert timeout_seconds == 300.0

        def evaluate(self, test_code, source_path):
            return MutationResult(
                total_mutants=2,
                killed_mutants=1,
                survived_mutants=1,
                timeout_mutants=0,
                mutation_score=0.5,
                surviving_mutant_names=("mutant",),
                wall_clock_seconds=0.1,
                stdout="",
                stderr="",
            )

    monkeypatch.setattr(
        experiment,
        "create_provider",
        lambda: SimpleNamespace(model="local-trial-model"),
    )
    monkeypatch.setattr(experiment, "SingleShotEngine", lambda provider: FakeEngine())
    monkeypatch.setattr(
        experiment,
        "AgentEngine",
        lambda provider, max_rounds, is_benchmark: FakeEngine(),
    )
    monkeypatch.setattr(experiment, "PynguinEngine", FakeEngine)
    monkeypatch.setattr(experiment, "WrongTestDetector", FakeWrongTestDetector)
    monkeypatch.setattr(experiment, "CoverageEvaluator", FakeCoverageEvaluator)
    monkeypatch.setattr(experiment, "MutationEvaluator", FakeMutationEvaluator)
    output_path = tmp_path / "results" / "trial.csv"

    summary = run_humaneval_experiment(dataset_path, output_path)

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert b"\r" not in output_path.read_bytes()
    assert len(summary.rows) == 3
    assert [row["engine_name"] for row in rows] == [
        "single-shot-llm",
        "agent-llm",
        "pynguin",
    ]
    assert all(row["status"] == "completed" for row in rows)
    assert all(row["model_name"] == "local-trial-model" for row in rows)
    assert all(row["wrong_test_status"] == "passed" for row in rows)
    assert all(row["mutation_score"] == "0.5" for row in rows)
    assert rows[1]["engine_settings"] == "max_rounds=3; benchmark_mode=true"
    assert events == [True, True, True]
