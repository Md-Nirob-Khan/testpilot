"""Greedily merge generated test cases by the mutants they kill."""

import ast
import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol

from testpilot.evaluator import (
    MutationEvaluator,
    MutationResult,
    WrongTestDetector,
    WrongTestResult,
)


class _MutationEvaluator(Protocol):
    def evaluate(self, test_code: str, source_path: Path) -> MutationResult:
        """Return mutant kill information for a test suite."""


class _WrongTestDetector(Protocol):
    def evaluate(
        self,
        test_code: str,
        source_path: Path,
        is_benchmark: bool,
    ) -> WrongTestResult:
        """Check candidate tests against the supplied implementation."""


@dataclass(frozen=True)
class MergeResult:
    """Contain the minimal greedy suite and its final mutation measurement."""

    test_code: str
    selected_test_names: tuple[str, ...]
    selected_test_count: int
    mutants_killed_by_selection: int
    mutants_available: int
    mutation_result: MutationResult


@dataclass(frozen=True)
class _Candidate:
    """Represent one isolated pytest case and its shared module context."""

    name: str
    test_node: ast.stmt
    prelude: tuple[ast.stmt, ...]
    killed_mutants: frozenset[str]


class BestOfMerger:
    """Select the smallest greedy set of tests killing the most mutants."""

    def __init__(
        self,
        mutation_evaluator: _MutationEvaluator | None = None,
        wrong_test_detector: _WrongTestDetector | None = None,
    ) -> None:
        """Initialize mutation scoring and original-source correctness checks."""
        self._mutation_evaluator = mutation_evaluator or MutationEvaluator()
        self._wrong_test_detector = wrong_test_detector or WrongTestDetector()

    def merge(
        self,
        source_path: Path,
        suites: Mapping[str, str],
    ) -> MergeResult:
        """Greedily choose passing test cases with the largest new mutant kills."""
        if not suites:
            raise ValueError("At least one generated suite is required")
        candidates: list[_Candidate] = []
        mutant_universe: set[str] = set()

        for engine_name, suite_code in suites.items():
            module = ast.parse(suite_code)
            prelude, test_nodes = _extract_test_nodes(module, engine_name)
            for candidate_name, test_node in test_nodes:
                candidate_code = _module_code(prelude, [test_node])
                correctness = self._wrong_test_detector.evaluate(
                    candidate_code,
                    source_path,
                    is_benchmark=False,
                )
                if correctness.status != "passed":
                    continue
                mutation = self._mutation_evaluator.evaluate(
                    candidate_code,
                    source_path,
                )
                killed = frozenset(mutation.killed_mutant_names)
                mutant_universe.update(killed)
                mutant_universe.update(mutation.surviving_mutant_names)
                mutant_universe.update(mutation.mutant_names)
                candidates.append(
                    _Candidate(
                        name=candidate_name,
                        test_node=test_node,
                        prelude=prelude,
                        killed_mutants=killed,
                    )
                )

        if not candidates:
            raise ValueError(
                "No generated test cases passed on the original source"
            )
        if not mutant_universe:
            raise ValueError("Mutation analysis found no mutants to merge")

        selected: list[_Candidate] = []
        remaining = list(candidates)
        killed_mutants: set[str] = set()
        while remaining:
            best = max(
                remaining,
                key=lambda candidate: (
                    len(candidate.killed_mutants - killed_mutants),
                    -remaining.index(candidate),
                ),
            )
            newly_killed = best.killed_mutants - killed_mutants
            if not newly_killed:
                break
            selected.append(best)
            killed_mutants.update(newly_killed)
            remaining.remove(best)

        if not selected:
            raise ValueError("No generated test case killed any mutants")

        prelude_by_key: dict[str, ast.stmt] = {}
        for candidate in selected:
            for node in candidate.prelude:
                prelude_by_key.setdefault(ast.dump(node), node)
        merged_code = _module_code(
            list(prelude_by_key.values()),
            [candidate.test_node for candidate in selected],
        )
        merged_correctness = self._wrong_test_detector.evaluate(
            merged_code,
            source_path,
            is_benchmark=False,
        )
        if merged_correctness.status != "passed":
            raise ValueError(
                "The merged suite did not pass on the original source: "
                f"{merged_correctness.explanation}"
            )
        final_mutation = self._mutation_evaluator.evaluate(
            merged_code,
            source_path,
        )
        return MergeResult(
            test_code=merged_code,
            selected_test_names=tuple(candidate.name for candidate in selected),
            selected_test_count=len(selected),
            mutants_killed_by_selection=len(killed_mutants),
            mutants_available=len(mutant_universe),
            mutation_result=final_mutation,
        )


def _extract_test_nodes(
    module: ast.Module,
    engine_name: str,
) -> tuple[tuple[ast.stmt, ...], list[tuple[str, ast.stmt]]]:
    """Separate shared module statements from collected pytest test cases."""
    prelude: list[ast.stmt] = []
    tests: list[tuple[str, ast.stmt]] = []
    engine_slug = _safe_identifier(engine_name)
    test_index = 0

    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            renamed = copy.deepcopy(node)
            test_index += 1
            original_name = node.name
            renamed.name = f"test_{engine_slug}_{_safe_identifier(original_name)}_{test_index}"
            tests.append((f"{engine_name}:{original_name}", renamed))
            continue

        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            test_methods = [
                member
                for member in node.body
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and member.name.startswith("test_")
            ]
            if test_methods:
                for method in test_methods:
                    cloned_class = copy.deepcopy(node)
                    selected_method = copy.deepcopy(method)
                    test_index += 1
                    original_name = f"{node.name}.{method.name}"
                    selected_method.name = (
                        f"test_{engine_slug}_{_safe_identifier(method.name)}_"
                        f"{test_index}"
                    )
                    cloned_class.name = (
                        f"Test{engine_slug.title()}{_safe_identifier(node.name)}"
                        f"{test_index}"
                    )
                    cloned_class.body = [
                        member
                        for member in cloned_class.body
                        if not (
                            isinstance(
                                member,
                                (ast.FunctionDef, ast.AsyncFunctionDef),
                            )
                            and member.name.startswith("test_")
                        )
                    ]
                    cloned_class.body.append(selected_method)
                    tests.append((f"{engine_name}:{original_name}", cloned_class))
                continue
        prelude.append(node)

    return tuple(prelude), tests


def _module_code(
    prelude: list[ast.stmt] | tuple[ast.stmt, ...],
    test_nodes: list[ast.stmt],
) -> str:
    """Format selected tests with their supporting imports and helper code."""
    return ast.unparse(ast.Module(body=[*prelude, *test_nodes], type_ignores=[]))


def _safe_identifier(value: str) -> str:
    """Convert an engine or test label to a valid Python identifier fragment."""
    identifier = re.sub(r"\W+", "_", value).strip("_")
    return identifier or "generated"
