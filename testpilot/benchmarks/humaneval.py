"""Load canonical HumanEval problems from the upstream JSONL dataset."""

import ast
import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class HumanEvalProblem:
    """Represent one HumanEval task and its canonical implementation."""

    task_id: str
    entry_point: str
    prompt: str
    canonical_solution: str

    @property
    def source_code(self) -> str:
        """Return the complete canonical module source."""
        return self.prompt + self.canonical_solution


def load_humaneval(
    dataset_path: Path,
    limit: int | None = None,
) -> tuple[HumanEvalProblem, ...]:
    """Load and validate HumanEval JSONL records, optionally taking a prefix."""
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"HumanEval dataset does not exist: {path}")
    if limit is not None and (
        isinstance(limit, bool) or not isinstance(limit, int) or limit < 1
    ):
        raise ValueError("limit must be a positive integer or None")

    records: list[HumanEvalProblem] = []
    seen_task_ids: set[str] = set()
    with _open_dataset(path) as dataset:
        for line_number, line in enumerate(dataset, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid HumanEval JSON on line {line_number}"
                ) from exc
            problem = _parse_problem(record, line_number)
            if problem.task_id in seen_task_ids:
                raise ValueError(
                    f"Duplicate HumanEval task ID on line {line_number}: "
                    f"{problem.task_id}"
                )
            seen_task_ids.add(problem.task_id)
            _validate_source(problem, line_number)
            records.append(problem)
            if limit is not None and len(records) >= limit:
                break

    if not records:
        raise ValueError("HumanEval dataset contains no problems")
    return tuple(records)


def _open_dataset(path: Path) -> TextIO:
    """Open plain or gzip-compressed UTF-8 JSONL data."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _parse_problem(record: object, line_number: int) -> HumanEvalProblem:
    """Validate one JSON object and construct a problem record."""
    if not isinstance(record, dict):
        raise ValueError(f"HumanEval line {line_number} must be a JSON object")
    fields = ("task_id", "entry_point", "prompt", "canonical_solution")
    values = {field: record.get(field) for field in fields}
    if any(not isinstance(value, str) or not value for value in values.values()):
        raise ValueError(
            f"HumanEval line {line_number} is missing required string fields"
        )
    return HumanEvalProblem(**values)


def _validate_source(problem: HumanEvalProblem, line_number: int) -> None:
    """Ensure the canonical source is valid and defines its entry point."""
    try:
        module = ast.parse(problem.source_code)
    except SyntaxError as exc:
        raise ValueError(
            f"Invalid canonical source on HumanEval line {line_number}"
        ) from exc
    if not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == problem.entry_point
        for node in module.body
    ):
        raise ValueError(
            f"Entry point {problem.entry_point!r} is missing on "
            f"HumanEval line {line_number}"
        )
