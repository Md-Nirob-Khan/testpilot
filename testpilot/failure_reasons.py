"""Explain failed generated tests in one readable line each, for the dashboard."""

import re
from pathlib import Path

from testpilot.sandbox import SandboxRunner, passing_test_selection

_SECTION = re.compile(r"^_{2,} (?:ERROR at \w+ of )?(.+?) _{2,}$")
_COMPARISON = re.compile(r"^assert (.+?) (==|!=|<=|>=|<|>) (.+)$")
_WHERE = re.compile(r"^\+\s+where (.+?) = (\w[\w.]*\(.*\))$")


def parse_failure_reasons(
    pytest_output: str,
    wrong_test_names: set[str] | None = None,
) -> tuple[str, ...]:
    """Turn pytest failure sections into lines like 'f(64) returned 12, but ...'.

    When wrong_test_names is given, only sections for those tests are kept.
    """
    reasons: list[str] = []
    for test_name, evidence in _failure_sections(pytest_output):
        base_name = test_name.split("[")[0]
        if wrong_test_names is not None and base_name not in wrong_test_names:
            continue
        reasons.append(f"{test_name}: {_describe(evidence)}")
    return tuple(reasons)


def collect_wrong_test_reasons(test_code: str, source_path: Path) -> tuple[str, ...]:
    """Run the suite in the sandbox and explain each wrong (non-xfail) test."""
    result = SandboxRunner().run(test_code, source_path)
    if result.timed_out:
        return ()
    selection = passing_test_selection(test_code, result.test_outcomes)
    names = None
    if selection is not None:
        names = {
            outcome.name.split("::")[-1].split("[")[0]
            for outcome in selection.wrong_test_outcomes
        }
    return parse_failure_reasons(result.stdout, names)


def _failure_sections(output: str) -> list[tuple[str, list[str]]]:
    """Split pytest output into (test name, 'E' lines) for each failure."""
    sections: list[tuple[str, list[str]]] = []
    for line in output.splitlines():
        header = _SECTION.match(line.strip())
        if header and not line.startswith(" "):
            sections.append((header.group(1), []))
        elif sections and line.startswith("E "):
            sections[-1][1].append(line[1:].strip())
    return [(name, lines) for name, lines in sections if lines]


def _describe(evidence: list[str]) -> str:
    """Describe the first error line, using 'where' lines to name the call."""
    first = evidence[0]
    calls = {}
    for line in evidence[1:]:
        match = _WHERE.match(line)
        if match:
            calls[match.group(1)] = match.group(2)
    comparison = _COMPARISON.match(first)
    if comparison:
        left, operator, right = comparison.groups()
        if operator == "==":
            if left in calls:
                return f"{calls[left]} returned {left}, but the test expected {right}"
            if right in calls:
                return f"{calls[right]} returned {right}, but the test expected {left}"
        return f"the check `{first}` failed"
    return first
