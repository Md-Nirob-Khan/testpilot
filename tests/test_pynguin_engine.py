"""Tests for the isolated Pynguin generation engine."""

import os
from pathlib import Path

import pytest

from testpilot.analyzer import analyze_source
from testpilot.engines import PynguinEngine
from testpilot.sandbox import PynguinSubprocessRunner


def _fake_pynguin(tmp_path: Path, body: str) -> Path:
    executable = tmp_path / "fake-pynguin-python"
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib\n"
        "import sys\n"
        "import os\n"
        f"{body}\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def test_pynguin_engine_returns_subprocess_output_and_zero_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n")
    executable = _fake_pynguin(
        tmp_path,
        "assert os.environ['PYNGUIN_DANGER_AWARE'] == '1'\n"
        "assert 'ANTHROPIC_API_KEY' not in os.environ\n"
        "assert pathlib.Path('testpilot_target.py').is_file()\n"
        "args = sys.argv\n"
        "assert args[args.index('--only-cover') + 1] == 'add'\n"
        "assert args[args.index('--seed') + 1] == '42'\n"
        "output_path = pathlib.Path(args[args.index('--output_path') + 1])\n"
        "output_path.mkdir(exist_ok=True)\n"
        "(output_path / 'test_testpilot_target.py').write_text("
        "'def test_generated():\\n    assert True\\n')",
    )
    engine = PynguinEngine(PynguinSubprocessRunner(python_executable=executable))
    function = analyze_source(
        "def add(left, right):\n    return left + right\n"
    )[0]
    original_danger_aware = os.environ.get("PYNGUIN_DANGER_AWARE")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-forwarded")

    suite = engine.generate(function, source_path)

    assert suite.test_code == "def test_generated():\n    assert True\n"
    assert suite.engine_name == "pynguin"
    assert suite.llm_tokens_used == 0
    assert suite.estimated_cost_usd == 0
    assert suite.wall_clock_seconds >= 0
    assert os.environ.get("PYNGUIN_DANGER_AWARE") == original_danger_aware


def test_pynguin_runner_times_out_and_cleans_up_process_group(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    executable = _fake_pynguin(tmp_path, "import time\ntime.sleep(2)")
    runner = PynguinSubprocessRunner(
        python_executable=executable,
        timeout_seconds=0.1,
        search_time_seconds=1,
    )

    with pytest.raises(TimeoutError, match="Pynguin exceeded"):
        runner.generate(source_path)


def test_pynguin_runner_rejects_missing_source(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Source file does not exist"):
        PynguinSubprocessRunner().generate(tmp_path / "missing.py")


def test_pynguin_runner_can_generate_without_a_function_filter(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    executable = _fake_pynguin(
        tmp_path,
        "assert '--only-cover' not in sys.argv\n"
        "args = sys.argv\n"
        "output_path = pathlib.Path(args[args.index('--output_path') + 1])\n"
        "(output_path / 'test_testpilot_target.py').write_text('VALUE = 1')",
    )

    result = PynguinSubprocessRunner(
        python_executable=executable,
        search_time_seconds=1,
    ).generate(source_path)

    assert result.test_code == "VALUE = 1"


@pytest.mark.parametrize("timeout_seconds", [0, float("inf"), float("nan")])
def test_pynguin_runner_rejects_invalid_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="Timeout must be a finite positive number"):
        PynguinSubprocessRunner(timeout_seconds=timeout_seconds)


@pytest.mark.parametrize("search_time_seconds", [0, -1, True, 1.5])
def test_pynguin_runner_rejects_invalid_search_time(
    search_time_seconds: int,
) -> None:
    with pytest.raises(ValueError, match="Search time must be a positive integer"):
        PynguinSubprocessRunner(search_time_seconds=search_time_seconds)


@pytest.mark.parametrize("seed", [True, 1.5, "42"])
def test_pynguin_runner_rejects_invalid_seed(seed: int) -> None:
    with pytest.raises(ValueError, match="Seed must be an integer"):
        PynguinSubprocessRunner(seed=seed)
