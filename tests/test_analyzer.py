"""Tests for source analysis."""

from pathlib import Path

import pytest

from testpilot.analyzer import SourceAnalysisError, analyze_file, analyze_source


def test_analyze_source_collects_signature_docstring_branches_and_complexity() -> None:
    source = '''\
def classify(value: int, /, enabled: bool = True) -> str:
    """Classify a value."""
    if value > 0 and enabled:
        return "positive"
    return "other"
'''

    function = analyze_source(source, Path("sample.py"))[0]

    assert function.name == "classify"
    assert [(argument.name, argument.annotation, argument.kind) for argument in function.arguments] == [
        ("value", "int", "positional_only"),
        ("enabled", "bool", "positional"),
    ]
    assert function.return_annotation == "str"
    assert function.docstring == "Classify a value."
    assert [branch.kind for branch in function.branches] == ["and", "if"]
    assert function.complexity == 3
    assert "def classify" in function.source_code


def test_analyze_source_includes_async_function_and_excludes_nested_function() -> None:
    source = '''\
async def outer(value):
    def inner():
        if value:
            return 1
    return value
'''

    functions = analyze_source(source)

    assert [function.name for function in functions] == ["outer"]
    assert functions[0].branches == ()


def test_analyze_source_reports_syntax_error() -> None:
    with pytest.raises(SourceAnalysisError, match="line 1"):
        analyze_source("def broken(:")


def test_analyze_file_reads_utf8_source(tmp_path: Path) -> None:
    source_path = tmp_path / "example.py"
    source_path.write_text("def greet(name: str) -> str:\n    return f'hi {name}'\n", encoding="utf-8")

    functions = analyze_file(source_path)

    assert functions[0].source_path == source_path
    assert functions[0].arguments[0].annotation == "str"


def test_analyze_source_returns_empty_when_there_are_no_top_level_functions() -> None:
    assert analyze_source("VALUE = 1\n") == []
