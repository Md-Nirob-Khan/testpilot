"""Parse Python functions into metadata used by generation engines."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from radon.complexity import cc_visit


class SourceAnalysisError(ValueError):
    """Raised when source cannot be analyzed into function metadata."""


@dataclass(frozen=True)
class ArgumentInfo:
    """Describe one function parameter."""

    name: str
    annotation: str | None
    kind: Literal[
        "positional_only",
        "positional",
        "var_positional",
        "keyword_only",
        "var_keyword",
    ]


@dataclass(frozen=True)
class BranchInfo:
    """Describe one branching construct in a function."""

    line: int
    kind: str
    condition: str
    alternatives: int


@dataclass(frozen=True)
class FunctionInfo:
    """Store source details and analysis results for a Python function."""

    name: str
    source_path: Path
    arguments: tuple[ArgumentInfo, ...]
    return_annotation: str | None
    docstring: str | None
    branches: tuple[BranchInfo, ...]
    complexity: int
    source_code: str


def analyze_file(source_path: Path) -> list[FunctionInfo]:
    """Analyze top-level functions in a Python source file."""
    path = Path(source_path)
    return analyze_source(
        path.read_text(encoding="utf-8"),
        source_path=path,
    )


def analyze_source(
    source: str,
    source_path: Path = Path("<memory>"),
) -> list[FunctionInfo]:
    """Analyze top-level synchronous and asynchronous functions in source."""
    try:
        module = ast.parse(source, filename=str(source_path))
    except SyntaxError as exc:
        location = f" at line {exc.lineno}" if exc.lineno is not None else ""
        raise SourceAnalysisError(f"Invalid Python syntax{location}: {exc.msg}") from exc

    return [
        _analyze_function(node, source, Path(source_path))
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def _analyze_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source: str,
    source_path: Path,
) -> FunctionInfo:
    function_source = ast.get_source_segment(source, node)
    if function_source is None:
        raise SourceAnalysisError(f"Could not retrieve source for function {node.name!r}")

    complexity_blocks = cc_visit(function_source)
    complexity = next(
        (
            block.complexity
            for block in complexity_blocks
            if block.name == node.name
        ),
        None,
    )
    if complexity is None:
        raise SourceAnalysisError(f"Could not calculate complexity for {node.name!r}")

    return FunctionInfo(
        name=node.name,
        source_path=source_path,
        arguments=_arguments(node.args),
        return_annotation=_annotation(node.returns),
        docstring=ast.get_docstring(node),
        branches=tuple(_branches(node, source)),
        complexity=complexity,
        source_code=function_source,
    )


def _arguments(arguments: ast.arguments) -> tuple[ArgumentInfo, ...]:
    positional_only_count = len(arguments.posonlyargs)
    positional_arguments = [
        *arguments.posonlyargs,
        *arguments.args,
    ]
    result = [
        ArgumentInfo(
            name=argument.arg,
            annotation=_annotation(argument.annotation),
            kind=(
                "positional_only"
                if index < positional_only_count
                else "positional"
            ),
        )
        for index, argument in enumerate(positional_arguments)
    ]

    if arguments.vararg is not None:
        result.append(
            ArgumentInfo(
                name=arguments.vararg.arg,
                annotation=_annotation(arguments.vararg.annotation),
                kind="var_positional",
            )
        )
    result.extend(
        ArgumentInfo(
            name=argument.arg,
            annotation=_annotation(argument.annotation),
            kind="keyword_only",
        )
        for argument in arguments.kwonlyargs
    )
    if arguments.kwarg is not None:
        result.append(
            ArgumentInfo(
                name=arguments.kwarg.arg,
                annotation=_annotation(arguments.kwarg.annotation),
                kind="var_keyword",
            )
        )
    return tuple(result)


def _annotation(node: ast.expr | None) -> str | None:
    return ast.unparse(node) if node is not None else None


def _branches(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    source: str,
) -> list[BranchInfo]:
    found: list[BranchInfo] = []
    pending = list(function.body)

    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, ast.If):
            found.append(_branch(node, source, "if", node.test, 2))
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            condition = (
                ast.Tuple(elts=[node.target, node.iter], ctx=ast.Load())
                if isinstance(node, (ast.For, ast.AsyncFor))
                else node.test
            )
            found.append(_branch(node, source, type(node).__name__.lower(), condition, 2))
        elif isinstance(node, ast.IfExp):
            found.append(_branch(node, source, "conditional", node.test, 2))
        elif isinstance(node, ast.BoolOp):
            found.append(
                _branch(
                    node,
                    source,
                    type(node.op).__name__.lower(),
                    node,
                    len(node.values),
                )
            )
        pending.extend(ast.iter_child_nodes(node))

    return sorted(found, key=lambda branch: (branch.line, branch.kind))


def _branch(
    node: ast.AST,
    source: str,
    kind: str,
    condition: ast.AST,
    alternatives: int,
) -> BranchInfo:
    return BranchInfo(
        line=getattr(node, "lineno", 0),
        kind=kind,
        condition=ast.get_source_segment(source, condition) or kind,
        alternatives=alternatives,
    )
