"""Tests for the Phase 1 command-line interface."""

import argparse
from pathlib import Path

import pytest

from testpilot.analyzer import analyze_source
from testpilot.cli import _select_function, main
from testpilot.llm import LLMResponse


def test_select_function_requires_name_if_multiple_functions() -> None:
    functions = analyze_source("def first():\n    pass\n\ndef second():\n    pass\n")
    parser = argparse.ArgumentParser()

    with pytest.raises(SystemExit) as exc:
        _select_function(functions, None, parser)

    assert exc.value.code == 2


def test_main_reports_no_functions(tmp_path: Path) -> None:
    source_path = tmp_path / "empty.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main(["generate", str(source_path)])

    assert exc.value.code == 2


def test_main_generates_and_runs_tests_in_sandbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")

    class FakeProvider:
        def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
            return LLMResponse(
                "from testpilot_target import add\n\n"
                "def test_add():\n"
                "    assert add(2, 3) == 5\n",
                7,
                5,
                0.001,
            )

    monkeypatch.setattr("testpilot.cli.create_provider", lambda _name: FakeProvider())

    exit_code = main(["generate", str(source_path), "--run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Sandbox: 1 passed" in captured.err
    assert "def test_add" in captured.out
