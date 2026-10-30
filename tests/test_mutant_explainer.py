"""Tests for actionable descriptions of surviving mutants."""

from testpilot.evaluator import explain_mutants


def test_explains_comparison_mutant_with_boundary_test_suggestion() -> None:
    explanation, = explain_mutants(
        [
            (
                "target.classify_mutmut_1",
                "--- target.py\n"
                "+++ target.py\n"
                "@@ -1,2 +1,2 @@\n"
                "-    if value > 0:\n"
                "+    if value >= 0:\n",
            )
        ]
    )

    assert explanation.mutant_name == "target.classify_mutmut_1"
    assert "comparison changes from `>` to `>=`" in explanation.description
    assert "where the compared values are equal" in explanation.missing_test_case
    assert "-    if value > 0:" in explanation.diff


def test_explainer_handles_diff_without_common_operator() -> None:
    explanation, = explain_mutants(
        [("target.mutant", "--- target.py\n+++ target.py\n-return 1\n+return 2\n")]
    )

    assert "changes from `return 1` to `return 2`" in explanation.description
    assert "differs between the original and mutated code" in (
        explanation.missing_test_case
    )
