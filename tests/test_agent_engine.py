"""Tests for iterative test generation and evaluator-driven feedback."""

from pathlib import Path

import pytest

from testpilot.analyzer import analyze_source
from testpilot.engines import AgentEngine
from testpilot.evaluator import CoverageResult, MutationResult, WrongTestResult
from testpilot.llm import LLMResponse
from testpilot.sandbox import SandboxResult


class FakeProvider:
    """Return queued generations and retain every prompt sent to the model."""

    def __init__(self, generations: list[str]) -> None:
        self.generations = iter(generations)
        self.prompts: list[tuple[str, str]] = []

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.prompts.append((system_prompt, user_prompt))
        return LLMResponse(next(self.generations), 3, 2, 0.01)


class FakeCoverageEvaluator:
    """Record raw suites and return a known coverage report."""

    def __init__(self) -> None:
        self.suites: list[str] = []
        self.source_paths: list[Path] = []

    def evaluate(self, test_code: str, _source_path: Path) -> CoverageResult:
        self.suites.append(test_code)
        self.source_paths.append(_source_path)
        return CoverageResult(
            tests_run=1,
            passed=1,
            failed=0,
            errors=0,
            skipped=0,
            line_covered=2,
            line_total=3,
            line_percent=66.7,
            branch_covered=1,
            branch_total=2,
            branch_percent=50.0,
            uncovered_lines=(4,),
            uncovered_branches=((2, 4),),
            returncode=0,
            wall_clock_seconds=0.1,
            stdout="",
            stderr="",
        )


class FakeMutationEvaluator:
    """Record raw suites and return queued mutation scores."""

    def __init__(self, scores: list[float]) -> None:
        self.scores = iter(scores)
        self.suites: list[str] = []
        self.source_paths: list[Path] = []

    def evaluate(self, test_code: str, _source_path: Path) -> MutationResult:
        self.suites.append(test_code)
        self.source_paths.append(_source_path)
        score = next(self.scores)
        total = 10
        killed = round(score * total)
        survived = total - killed
        return MutationResult(
            total_mutants=total,
            killed_mutants=killed,
            survived_mutants=survived,
            timeout_mutants=0,
            mutation_score=score,
            surviving_mutant_names=(
                ("mutant_1",) if survived else ()
            ),
            wall_clock_seconds=0.1,
            stdout="",
            stderr="",
        )


class FakeWrongTestDetector:
    """Return queued raw-suite correctness results."""

    def __init__(self, results: list[WrongTestResult]) -> None:
        self.results = iter(results)
        self.calls: list[tuple[str, Path, bool]] = []

    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        is_benchmark: bool,
    ) -> WrongTestResult:
        self.calls.append((test_code, source_path, is_benchmark))
        return next(self.results)


def _function_and_source(tmp_path: Path):
    source_path = tmp_path / "subject.py"
    source = "def double(value):\n    return value * 2\n"
    source_path.write_text(source, encoding="utf-8")
    function_info = analyze_source(source, source_path)[0]
    return function_info, source_path


def _wrong_test_result(status: str, failing_tests: int = 0) -> WrongTestResult:
    return WrongTestResult(
        status=status,
        failing_tests=failing_tests,
        sandbox_result=SandboxResult(
            tests_run=1,
            passed=1 - bool(failing_tests),
            failed=failing_tests,
            errors=0,
            skipped=0,
            returncode=0 if status == "passed" else 1,
            timed_out=False,
            wall_clock_seconds=0.1,
            stdout="AssertionError: incorrect expectation",
            stderr="",
        ),
        explanation="Known test outcome",
    )


def test_agent_keeps_best_mutation_score_and_stops_when_score_stalls(
    tmp_path: Path,
) -> None:
    function_info, source_path = _function_and_source(tmp_path)
    generated = ["raw round one", "raw round two", "raw round three"]
    provider = FakeProvider(generated)
    coverage = FakeCoverageEvaluator()
    mutation = FakeMutationEvaluator([0.4, 0.8, 0.8])
    wrong_tests = FakeWrongTestDetector([_wrong_test_result("passed")] * 3)

    suite = AgentEngine(
        provider,
        coverage_evaluator=coverage,
        mutation_evaluator=mutation,
        wrong_test_detector=wrong_tests,
    ).generate(function_info, source_path)

    assert suite.test_code == "raw round two"
    assert suite.engine_name == "agent-llm"
    assert suite.rounds == 3
    assert suite.llm_tokens_used == 15
    assert suite.estimated_cost_usd == pytest.approx(0.03)
    assert suite.wrong_test_count == 0
    assert suite.needs_human_review_count == 0
    assert wrong_tests.calls == [
        (raw, source_path, False) for raw in generated
    ]
    assert coverage.suites == generated
    assert mutation.suites == generated
    assert coverage.source_paths == mutation.source_paths == [source_path] * 3
    assert "raw round one" in provider.prompts[1][1]
    assert "Uncovered source lines: (4,)" in provider.prompts[1][1]
    assert "Surviving mutants: ('mutant_1',)" in provider.prompts[1][1]


def test_agent_scores_raw_wrong_tests_then_uses_feedback(
    tmp_path: Path,
) -> None:
    function_info, source_path = _function_and_source(tmp_path)
    generated = ["raw incorrect suite", "raw passing suite"]
    provider = FakeProvider(generated)
    coverage = FakeCoverageEvaluator()
    mutation = FakeMutationEvaluator([0.7])
    wrong_tests = FakeWrongTestDetector(
        [
            _wrong_test_result("needs_human_review", failing_tests=1),
            _wrong_test_result("passed"),
        ]
    )

    suite = AgentEngine(
        provider,
        max_rounds=2,
        coverage_evaluator=coverage,
        mutation_evaluator=mutation,
        wrong_test_detector=wrong_tests,
    ).generate(function_info, source_path)

    assert [call[0] for call in wrong_tests.calls] == generated
    assert coverage.suites == ["raw passing suite"]
    assert mutation.suites == ["raw passing suite"]
    assert coverage.source_paths == mutation.source_paths == [source_path]
    assert suite.test_code == "raw passing suite"
    assert suite.rounds == 2
    assert suite.wrong_test_count == 0
    assert suite.needs_human_review_count == 1
    assert "raw incorrect suite" in provider.prompts[1][1]
    assert "needs_human_review" in provider.prompts[1][1]
    assert "AssertionError: incorrect expectation" in provider.prompts[1][1]


def test_agent_returns_last_raw_suite_if_all_rounds_fail(
    tmp_path: Path,
) -> None:
    function_info, source_path = _function_and_source(tmp_path)
    provider = FakeProvider(["first raw suite", "last raw suite"])
    coverage = FakeCoverageEvaluator()
    mutation = FakeMutationEvaluator([])
    wrong_tests = FakeWrongTestDetector(
        [
            _wrong_test_result("wrong_test", failing_tests=2),
            _wrong_test_result("wrong_test", failing_tests=1),
        ]
    )

    suite = AgentEngine(
        provider,
        max_rounds=2,
        is_benchmark=True,
        coverage_evaluator=coverage,
        mutation_evaluator=mutation,
        wrong_test_detector=wrong_tests,
    ).generate(function_info, source_path)

    assert suite.test_code == "last raw suite"
    assert suite.rounds == 2
    assert suite.wrong_test_count == 3
    assert suite.needs_human_review_count == 0
    assert all(call[2] for call in wrong_tests.calls)
    assert coverage.suites == []
    assert mutation.suites == []


@pytest.mark.parametrize("max_rounds", [0, -1, 1.5, True])
def test_agent_rejects_invalid_round_limit(max_rounds: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        AgentEngine(FakeProvider([]), max_rounds=max_rounds)


def test_agent_rejects_empty_generation(tmp_path: Path) -> None:
    function_info, source_path = _function_and_source(tmp_path)
    provider = FakeProvider(["```python\n```"])
    wrong_tests = FakeWrongTestDetector([])

    with pytest.raises(ValueError, match="empty test suite"):
        AgentEngine(provider, wrong_test_detector=wrong_tests).generate(
            function_info,
            source_path,
        )

    assert wrong_tests.calls == []


def test_agent_integrates_real_subprocess_evaluators(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source = (
        "def absolute(value: int) -> int:\n"
        "    if value < 0:\n"
        "        return -value\n"
        "    return value\n"
    )
    source_path.write_text(source, encoding="utf-8")
    function_info = analyze_source(source, source_path)[0]
    tests = (
        "from testpilot_target import absolute\n\n"
        "def test_absolute():\n"
        "    assert absolute(-3) == 3\n"
        "    assert absolute(0) == 0\n"
        "    assert absolute(4) == 4\n"
    )

    suite = AgentEngine(FakeProvider([tests]), max_rounds=1).generate(
        function_info,
        source_path,
    )

    assert suite.test_code == tests.strip()
    assert suite.rounds == 1
    assert suite.wrong_test_count == 0
    assert suite.needs_human_review_count == 0
