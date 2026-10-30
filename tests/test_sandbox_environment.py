"""Tests for environment isolation when executing untrusted code."""

import os
from pathlib import Path

from testpilot.sandbox import SandboxRunner, isolated_subprocess_environment


def test_isolated_environment_keeps_runtime_variables_but_drops_credentials(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("PYTHONPATH", "/untrusted/path")

    environment = isolated_subprocess_environment()

    assert environment["PATH"] == "/usr/bin"
    assert "ANTHROPIC_API_KEY" not in environment
    assert "GITHUB_TOKEN" not in environment
    assert "PYTHONPATH" not in environment
    assert os.environ["ANTHROPIC_API_KEY"] == "secret"


def test_sandbox_does_not_expose_parent_credentials(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-for-generated-code")
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = (
        "import os\n\n"
        "def test_credentials_are_not_inherited():\n"
        "    assert 'ANTHROPIC_API_KEY' not in os.environ\n"
    )

    result = SandboxRunner().run(test_code, source_path)

    assert result.returncode == 0
    assert result.passed == 1
