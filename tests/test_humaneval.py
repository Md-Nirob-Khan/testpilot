"""Tests for HumanEval loading and experiment CSV reporting."""

import csv
import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from testpilot.engines.base import GeneratedSuite
from testpilot.experiment import (
    _format_error,
    _run_one,
    run_humaneval_experiment,
)
from testpilot.evaluator import MutationResult
from testpilot.benchmarks import load_humaneval
from testpilot.analyzer import analyze_source
from testpilot.benchmarks import HumanEvalProblem
from testpilot.sandbox import SandboxResult, TestOutcome
from testpilot.llm import LLMProviderError


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
    remaining = load_humaneval(dataset_path, limit=1, offset=1)
    assert remaining[0].task_id == "HumanEval/1"


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


def test_final_ollama_refusal_is_marked_as_infrastructure_error(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "testpilot_target.py"
    source_path.write_text(_record()["prompt"] + _record()["canonical_solution"])
    function = analyze_source(source_path.read_text(), source_path)[0]
    problem = HumanEvalProblem(
        task_id="HumanEval/0",
        entry_point="add",
        prompt=_record()["prompt"],
        canonical_solution=_record()["canonical_solution"],
    )

    class RefusingEngine:
        def generate(self, function_info, target_path):
            raise LLMProviderError(
                "Ollama request failed: [Errno 61] Connection refused"
            )

    row = _run_one(
        problem=problem,
        function=function,
        source_path=source_path,
        engine_name="single-shot-llm",
        engine_settings="one generation attempt",
        engine=RefusingEngine(),
        model_name="test-model",
        run_date="2026-10-30",
        run_started_at="2026-10-30T00:00:00-05:00",
    )

    assert row.status == "infrastructure_error"
    assert "Connection refused" in row.error


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
            return SimpleNamespace(
                status="passed",
                failing_tests=0,
                sandbox_result=SandboxResult(
                    tests_run=1,
                    passed=1,
                    failed=0,
                    errors=0,
                    skipped=0,
                    returncode=0,
                    timed_out=False,
                    wall_clock_seconds=0.1,
                    stdout="",
                    stderr="",
                    test_outcomes=(
                        TestOutcome("test_generated::test_add", "passed"),
                    ),
                ),
            )

    class FakeCoverageEvaluator:
        def __init__(self, timeout_seconds):
            assert timeout_seconds == 30.0

        def evaluate(self, test_code, source_path, deselected_test_ids=()):
            return SimpleNamespace(line_percent=75.0, branch_percent=50.0)

    class FakeMutationEvaluator:
        def __init__(self, timeout_seconds):
            assert timeout_seconds == 300.0

        def evaluate(self, test_code, source_path, deselected_test_ids=()):
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
        lambda: SimpleNamespace(
            model="local-trial-model",
            temperature=0.0,
            seed=42,
        ),
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

    summary = run_humaneval_experiment(
        dataset_path,
        output_path,
        task_ids=["HumanEval/0"],
    )

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
    assert all(row["temperature"] == "0.0" for row in rows)
    assert all(row["seed"] == "42" for row in rows)
    assert all(row["wrong_test_status"] == "passed" for row in rows)
    assert all(row["passing_test_count"] == "1" for row in rows)
    assert all(row["expected_failure_count"] == "0" for row in rows)
    assert all(row["no_scorable_tests"] == "False" for row in rows)
    assert all(row["wrong_test_reasons_json"] == "[]" for row in rows)
    assert all(row["line_percent"] == "75.0" for row in rows)
    assert all(row["branch_percent"] == "50.0" for row in rows)
    assert all(row["mutation_score"] == "0.5" for row in rows)
    assert rows[1]["engine_settings"] == "max_rounds=3; benchmark_mode=true"
    assert events == [True, True, True]


def test_experiment_scores_passing_cases_and_records_failure_reasons(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.experiment as experiment

    dataset_path = tmp_path / "HumanEval.jsonl"
    dataset_path.write_text(json.dumps(_record()), encoding="utf-8")
    raw_suite = (
        "def test_wrong():\n"
        "    assert 1 == 2\n\n"
        "def test_right():\n"
        "    assert 1 == 1\n"
    )
    evaluated_suites: list[tuple[str, tuple[str, ...]]] = []

    class FakeEngine:
        def generate(self, function_info, source_path):
            return GeneratedSuite(
                test_code=raw_suite,
                engine_name="fake",
                wall_clock_seconds=0.25,
                llm_tokens_used=0,
                estimated_cost_usd=0.0,
            )

    class FakeWrongTestDetector:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, test_code, source_path, is_benchmark):
            assert is_benchmark
            return SimpleNamespace(
                status="wrong_test",
                failing_tests=1,
                sandbox_result=SandboxResult(
                    tests_run=2,
                    passed=1,
                    failed=1,
                    errors=0,
                    skipped=0,
                    returncode=1,
                    timed_out=False,
                    wall_clock_seconds=0.1,
                    stdout="",
                    stderr="",
                    test_outcomes=(
                        TestOutcome(
                            "test_generated::test_wrong",
                            "failed",
                            "assertion_failure",
                        ),
                        TestOutcome("test_generated::test_right", "passed"),
                    ),
                ),
            )

    class FakeCoverageEvaluator:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, test_code, source_path, deselected_test_ids=()):
            evaluated_suites.append((test_code, deselected_test_ids))
            return SimpleNamespace(line_percent=100.0, branch_percent=100.0)

    class FakeMutationEvaluator:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, test_code, source_path, deselected_test_ids=()):
            evaluated_suites.append((test_code, deselected_test_ids))
            return MutationResult(
                total_mutants=1,
                killed_mutants=1,
                survived_mutants=0,
                timeout_mutants=0,
                mutation_score=1.0,
                surviving_mutant_names=(),
                wall_clock_seconds=0.1,
                stdout="",
                stderr="",
            )

    monkeypatch.setattr(
        experiment,
        "create_provider",
        lambda: SimpleNamespace(model="test-model"),
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

    summary = run_humaneval_experiment(
        dataset_path,
        tmp_path / "trial.csv",
        task_ids=["HumanEval/0"],
    )

    assert all(row.status == "completed" for row in summary.rows)
    assert all(row.wrong_test_count == 1 for row in summary.rows)
    assert all(row.passing_test_count == 1 for row in summary.rows)
    assert all(row.expected_failure_count == 0 for row in summary.rows)
    assert all(row.mutation_score == 1.0 for row in summary.rows)
    assert all(
        json.loads(row.wrong_test_reasons_json)
        == [
            {
                "test_name": "test_generated::test_wrong",
                "reason": "assertion_failure",
            }
        ]
        for row in summary.rows
    )
    assert len(evaluated_suites) == 6
    assert all(suite == raw_suite for suite, _ in evaluated_suites)
    assert all(
        deselected == ("tests/test_generated.py::test_wrong",)
        for _, deselected in evaluated_suites
    )


def test_experiment_flags_passing_tests_that_never_cover_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.experiment as experiment

    dataset_path = tmp_path / "HumanEval.jsonl"
    dataset_path.write_text(json.dumps(_record()), encoding="utf-8")

    class FakeEngine:
        def generate(self, function_info, source_path):
            return GeneratedSuite(
                test_code="def test_unrelated():\n    assert True\n",
                engine_name="fake",
                wall_clock_seconds=0.1,
                llm_tokens_used=0,
                estimated_cost_usd=0.0,
            )

    class FakeWrongTestDetector:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, test_code, source_path, is_benchmark):
            return SimpleNamespace(
                status="passed",
                failing_tests=0,
                expected_failure_count=0,
                sandbox_result=SandboxResult(
                    tests_run=1,
                    passed=1,
                    failed=0,
                    errors=0,
                    skipped=0,
                    returncode=0,
                    timed_out=False,
                    wall_clock_seconds=0.1,
                    stdout="",
                    stderr="",
                    test_outcomes=(
                        TestOutcome("test_generated::test_unrelated", "passed"),
                    ),
                ),
            )

    class NoTargetCoverageEvaluator:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, test_code, source_path, deselected_test_ids=()):
            raise RuntimeError("Could not produce coverage JSON: No data to report.")

    class UnexpectedMutationEvaluator:
        def __init__(self, timeout_seconds):
            pass

        def evaluate(self, *args, **kwargs):
            raise AssertionError("Mutation scoring must be skipped")

    monkeypatch.setattr(
        experiment,
        "create_provider",
        lambda: SimpleNamespace(model="test-model", temperature=0.0, seed=42),
    )
    monkeypatch.setattr(experiment, "SingleShotEngine", lambda provider: FakeEngine())
    monkeypatch.setattr(
        experiment,
        "AgentEngine",
        lambda provider, max_rounds, is_benchmark: FakeEngine(),
    )
    monkeypatch.setattr(experiment, "PynguinEngine", FakeEngine)
    monkeypatch.setattr(experiment, "WrongTestDetector", FakeWrongTestDetector)
    monkeypatch.setattr(experiment, "CoverageEvaluator", NoTargetCoverageEvaluator)
    monkeypatch.setattr(
        experiment,
        "MutationEvaluator",
        UnexpectedMutationEvaluator,
    )

    summary = run_humaneval_experiment(
        dataset_path,
        tmp_path / "no-scorable.csv",
        task_ids=["HumanEval/0"],
    )

    assert len(summary.rows) == 3
    assert all(row.status == "completed" for row in summary.rows)
    assert all(row.passing_test_count == 1 for row in summary.rows)
    assert all(row.no_scorable_tests for row in summary.rows)
    assert all(row.line_percent == 0.0 for row in summary.rows)
    assert all(row.branch_percent == 0.0 for row in summary.rows)
    assert all(row.mutation_score == 0.0 for row in summary.rows)


def test_experiment_excludes_xfails_for_every_engine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import testpilot.experiment as experiment

    dataset_path = tmp_path / "HumanEval.jsonl"
    dataset_path.write_text(json.dumps(_record()), encoding="utf-8")
    xfail_suite = (
        "import pytest\n\n"
        "@pytest.mark.xfail(strict=True)\n"
        "def test_expected_exception():\n"
        "    raise RuntimeError('expected')\n"
    )

    class FakeEngine:
        def generate(self, function_info, source_path):
            return GeneratedSuite(
                test_code=xfail_suite,
                engine_name="fake",
                wall_clock_seconds=0.1,
                llm_tokens_used=0,
                estimated_cost_usd=0.0,
            )

    monkeypatch.setattr(
        experiment,
        "create_provider",
        lambda: SimpleNamespace(model="test-model"),
    )
    monkeypatch.setattr(experiment, "SingleShotEngine", lambda provider: FakeEngine())
    monkeypatch.setattr(
        experiment,
        "AgentEngine",
        lambda provider, max_rounds, is_benchmark: FakeEngine(),
    )
    monkeypatch.setattr(experiment, "PynguinEngine", FakeEngine)

    output_path = tmp_path / "xfail-results.csv"
    summary = run_humaneval_experiment(
        dataset_path,
        output_path,
        task_ids=["HumanEval/0"],
    )

    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(summary.rows) == 3
    assert all(row.status == "completed" for row in summary.rows)
    assert all(row.wrong_test_status == "passed" for row in summary.rows)
    assert all(row.wrong_test_count == 0 for row in summary.rows)
    assert all(row.expected_failure_count == 1 for row in summary.rows)
    assert all(row.passing_test_count == 0 for row in summary.rows)
    assert all(row.no_scorable_tests for row in summary.rows)
    assert all(row.line_percent == 0 for row in summary.rows)
    assert all(row.branch_percent == 0 for row in summary.rows)
    assert all(row.mutation_score == 0 for row in summary.rows)
    assert all(row["expected_failure_count"] == "1" for row in rows)
    assert all(row["no_scorable_tests"] == "True" for row in rows)
