"""Turn mutmut source diffs into readable descriptions and test suggestions."""

import re
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class MutantExplanation:
    """Describe a surviving mutation and a test likely to distinguish it."""

    mutant_name: str
    description: str
    missing_test_case: str
    diff: str


def explain_mutants(
    mutant_diffs: Sequence[tuple[str, str]],
) -> tuple[MutantExplanation, ...]:
    """Explain every surviving mutant using its original-to-mutated diff."""
    return tuple(
        _explain_mutant(mutant_name, diff)
        for mutant_name, diff in mutant_diffs
    )


def _explain_mutant(mutant_name: str, diff: str) -> MutantExplanation:
    removed, added = _changed_lines(diff)
    if removed and added:
        old_line = removed[0]
        new_line = added[0]
        description, suggestion = _describe_change(old_line, new_line)
    else:
        description = (
            "The mutant changes target code that the generated suite did not "
            "distinguish from the original."
        )
        suggestion = (
            "Add a test that reaches the changed source location and asserts "
            "the expected behavior."
        )
    return MutantExplanation(
        mutant_name=mutant_name,
        description=description,
        missing_test_case=suggestion,
        diff=diff,
    )


def _changed_lines(diff: str) -> tuple[list[str], list[str]]:
    """Extract removed and added source lines from a unified diff."""
    removed: list[str] = []
    added: list[str] = []
    for line in diff.splitlines():
        if line.startswith(("---", "+++")):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())
    return removed, added


def _describe_change(old_line: str, new_line: str) -> tuple[str, str]:
    """Translate common mutation operators into actionable test guidance."""
    old_operator, new_operator = _changed_operator(old_line, new_line)
    if old_operator and new_operator:
        if {old_operator, new_operator}.issubset({">", ">=", "<", "<="}):
            return (
                f"The comparison changes from `{old_operator}` to "
                f"`{new_operator}`, changing behavior at the boundary.",
                "Add a boundary-value test where the compared values are equal "
                "and assert the expected result.",
            )
        if {old_operator, new_operator}.issubset({"==", "!="}):
            return (
                f"The equality check changes from `{old_operator}` to "
                f"`{new_operator}`, reversing its result.",
                "Add tests for both equal and unequal values and assert the "
                "expected behavior for each.",
            )
        if {old_operator, new_operator}.issubset({"+", "-"}):
            return (
                f"The arithmetic operation changes from `{old_operator}` to "
                f"`{new_operator}`.",
                "Add a test with non-zero, unequal operands and assert the "
                "exact expected arithmetic result.",
            )
        if {old_operator, new_operator}.issubset({"*", "/"}):
            return (
                f"The arithmetic operation changes from `{old_operator}` to "
                f"`{new_operator}`.",
                "Add a test with operands for which multiplication and division "
                "produce different results.",
            )
    if old_line and new_line:
        return (
            f"The source changes from `{old_line}` to `{new_line}`, but the "
            "generated suite still passes.",
            "Add a test that reaches this statement and asserts an outcome "
            "that differs between the original and mutated code.",
        )
    return (
        "The mutant changes target code that the generated suite did not "
        "distinguish from the original.",
        "Add a test that reaches the changed source location and asserts the "
        "expected behavior.",
    )


def _changed_operator(old_line: str, new_line: str) -> tuple[str | None, str | None]:
    """Return a recognized operator pair changed between source lines."""
    operators = ("==", "!=", ">=", "<=", ">", "<", "+", "-", "*", "/")
    old_operators = re.findall(r"==|!=|>=|<=|[><+\-*/]", old_line)
    new_operators = re.findall(r"==|!=|>=|<=|[><+\-*/]", new_line)
    for old_operator, new_operator in zip(old_operators, new_operators):
        if old_operator != new_operator and (
            old_operator in operators and new_operator in operators
        ):
            return old_operator, new_operator
    return None, None
