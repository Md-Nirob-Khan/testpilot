"""Tests for greedy best-of suite merging."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from testpilot.evaluator import (
    MutationEvaluator,
    MutationResult,
    WrongTestDetector,
)
from testpilot.merge import BestOfMerger


class _Detector:
    def evaluate(self, test_code: str, source_path: Path, is_benchmark: bool):
        return SimpleNamespace(
            status="passed",
            explanation="All tests passed.",
        )


class _MutationScorer:
    all_mutants = {"mutant_a", "mutant_b", "mutant_c"}

    def evaluate(self, test_code: str, source_path: Path) -> MutationResult:
        if "test_single" in test_code:
            killed = {"mutant_a"}
        elif "test_pair" in test_code:
            killed = {"mutant_b", "mutant_c"}
        elif "test_redundant" in test_code:
            killed = {"mutant_a"}
        else:
            killed = {"mutant_a", "mutant_b", "mutant_c"}
        surviving = self.all_mutants - killed
        return MutationResult(
            total_mutants=len(self.all_mutants),
            killed_mutants=len(killed),
            survived_mutants=len(surviving),
            timeout_mutants=0,
            mutation_score=len(killed) / len(self.all_mutants),
            surviving_mutant_names=tuple(sorted(surviving)),
            wall_clock_seconds=0.1,
            stdout="",
            stderr="",
            killed_mutant_names=tuple(sorted(killed)),
        )


def test_merger_uses_greedy_mutant_set_cover_and_validates_final_suite(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def value():\n    return 1\n", encoding="utf-8")
    suites = {
        "llm": (
            "from testpilot_target import value\n"
            "def test_single():\n    assert value() == 1\n"
            "def test_redundant():\n    assert value() == 1\n"
        ),
        "pynguin": (
            "from testpilot_target import value\n"
            "def test_pair():\n    assert value() == 1\n"
        ),
    }

    result = BestOfMerger(_MutationScorer(), _Detector()).merge(
        source_path,
        suites,
    )

    assert result.selected_test_names == ("pynguin:test_pair", "llm:test_single")
    assert result.selected_test_count == 2
    assert result.mutants_killed_by_selection == 3
    assert result.mutants_available == 3
    assert "test_pynguin_test_pair_1" in result.test_code
    assert "test_llm_test_single_1" in result.test_code
    assert "test_llm_test_redundant_2" not in result.test_code


def test_merger_rejects_missing_test_cases(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="No generated test cases passed"):
        BestOfMerger(_MutationScorer(), _Detector()).merge(
            source_path,
            {"empty": "VALUE = 1\n"},
        )


def test_merger_known_answer_combines_cases_to_kill_all_mutants(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text(
        "def classify(value):\n"
        "    if value > 0:\n"
        "        return 'positive'\n"
        "    return 'non-positive'\n",
        encoding="utf-8",
    )
    suites = {
        "single-shot-llm": (
            "from testpilot_target import classify\n\n"
            "def test_positive():\n"
            "    assert classify(1) == 'positive'\n"
        ),
        "pynguin": (
            "from testpilot_target import classify\n\n"
            "def test_non_positive():\n"
            "    assert classify(0) == 'non-positive'\n"
        ),
    }

    result = BestOfMerger(
        MutationEvaluator(timeout_seconds=120),
        WrongTestDetector(),
    ).merge(source_path, suites)

    assert result.selected_test_count == 2
    assert result.mutation_result.total_mutants > 0
    assert result.mutation_result.killed_mutants == (
        result.mutation_result.total_mutants
    )
    assert result.mutation_result.survived_mutants == 0
    assert result.mutants_killed_by_selection == result.mutants_available
