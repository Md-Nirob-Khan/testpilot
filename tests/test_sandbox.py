"""Tests for safe subprocess execution of generated tests."""

from pathlib import Path

import pytest

from testpilot.sandbox import SandboxRunner


def test_sandbox_runs_passing_generated_tests(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n", encoding="utf-8")
    test_code = (
        "from testpilot_target import add\n\n"
        "def test_add():\n"
        "    assert add(2, 3) == 5\n"
    )

    result = SandboxRunner().run(test_code, source_path)

    assert result.tests_run == 1
    assert result.passed == 1
    assert result.failed == result.errors == result.skipped == 0
    assert result.returncode == 0
    assert not result.timed_out
    assert result.test_outcomes[0].name.endswith("::test_add")
    assert result.test_outcomes[0].status == "passed"


def test_sandbox_reports_assertion_failures(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def answer():\n    return 42\n", encoding="utf-8")

    result = SandboxRunner().run(
        "from testpilot_target import answer\n"
        "def test_answer():\n"
        "    assert answer() == 0\n",
        source_path,
    )

    assert result.tests_run == 1
    assert result.failed == 1
    assert result.returncode != 0
    assert "AssertionError" in result.stdout
    assert result.test_outcomes[0].status == "failed"
    assert result.test_outcomes[0].failure_kind == "assertion_failure"


def test_sandbox_classifies_missing_target_import_as_import_error(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("def add(left, right):\n    return left + right\n")
    test_code = "def test_add():\n    assert add(2, 3) == 5\n"

    result = SandboxRunner().run(test_code, source_path)

    assert result.failed == 1
    assert result.test_outcomes[0].failure_kind == "import_error"


def test_sandbox_does_not_label_runtime_exception_as_assertion_failure(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n")

    result = SandboxRunner().run(
        "def test_runtime_error():\n"
        "    raise TypeError('unexpected argument shape')\n",
        source_path,
    )

    assert result.failed == 1
    assert result.test_outcomes[0].failure_kind == "test_error"


@pytest.mark.parametrize(
    ("test_code", "failure_kind"),
    [
        ("def test_invalid(:\n    pass\n", "syntax_error"),
        (
            "import missing_testpilot_dependency\n"
            "def test_value():\n    pass\n",
            "import_error",
        ),
    ],
)
def test_sandbox_classifies_collection_errors(
    tmp_path: Path,
    test_code: str,
    failure_kind: str,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")

    result = SandboxRunner().run(test_code, source_path)

    assert result.errors == 1
    assert result.test_outcomes[0].failure_kind == failure_kind


def test_sandbox_selects_only_passing_test_cases(tmp_path: Path) -> None:
    from testpilot.sandbox import passing_test_selection

    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = (
        "import pytest\n"
        "from testpilot_target import VALUE\n\n"
        "def helper():\n"
        "    return VALUE\n\n"
        "def test_wrong():\n"
        "    assert helper() == 0\n\n"
        "def test_right():\n"
        "    assert helper() == 1\n"
    )
    result = SandboxRunner().run(test_code, source_path)

    selection = passing_test_selection(test_code, result.test_outcomes)

    assert selection is not None
    assert selection.passing_test_count == 1
    assert selection.for_test_file("test_generated.py") == (
        "test_generated.py::test_wrong",
    )

    selected_result = SandboxRunner().run(
        test_code,
        source_path,
        selection.for_test_file("test_generated.py"),
    )
    assert selected_result.tests_run == 1
    assert selected_result.passed == 1
    assert selected_result.failed == 0


def test_passing_selection_deselects_only_the_failing_parameter_case() -> None:
    from testpilot.sandbox import TestOutcome, passing_test_selection

    selection = passing_test_selection(
        (
            "import pytest\n"
            "@pytest.mark.parametrize('value', ['bad', 'good'])\n"
            "def test_param(value):\n"
            "    assert value\n"
        ),
        (
            TestOutcome("test_generated::test_param[bad]", "failed"),
            TestOutcome("test_generated::test_param[good]", "passed"),
        )
    )

    assert selection is not None
    assert selection.passing_test_count == 1
    assert selection.for_test_file("tests/test_generated.py") == (
        "tests/test_generated.py::test_param[bad]",
    )


def test_passing_selection_maps_test_class_nodeids() -> None:
    from testpilot.sandbox import TestOutcome, passing_test_selection

    selection = passing_test_selection(
        (
            "class TestGenerated:\n"
            "    def test_wrong(self):\n"
            "        assert False\n"
            "    def test_right(self):\n"
            "        assert True\n"
        ),
        (
            TestOutcome(
                "test_generated.TestGenerated::test_wrong",
                "failed",
                "assertion_failure",
            ),
            TestOutcome("test_generated.TestGenerated::test_right", "passed"),
        )
    )

    assert selection is not None
    assert selection.for_test_file("tests/test_generated.py") == (
        "tests/test_generated.py::TestGenerated::test_wrong",
    )


def test_xfail_marked_test_is_counted_separately_and_not_as_wrong(
    tmp_path: Path,
) -> None:
    from testpilot.evaluator import WrongTestDetector
    from testpilot.sandbox import passing_test_selection

    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = (
        "import pytest\n\n"
        "@pytest.mark.xfail(strict=True)\n"
        "def test_expected_exception():\n"
        "    raise RuntimeError('expected')\n"
    )

    correctness = WrongTestDetector().evaluate(
        test_code,
        source_path,
        is_benchmark=True,
    )
    selection = passing_test_selection(
        test_code,
        correctness.sandbox_result.test_outcomes,
    )

    assert correctness.status == "passed"
    assert correctness.failing_tests == 0
    assert correctness.expected_failure_count == 1
    assert selection is not None
    assert selection.expected_failure_count == 1
    assert selection.wrong_test_count == 0
    assert selection.passing_test_count == 0
    assert selection.for_test_file("tests/test_generated.py") == (
        "tests/test_generated.py::test_expected_exception",
    )


def test_parametrized_xfail_excludes_only_its_case(tmp_path: Path) -> None:
    from testpilot.sandbox import passing_test_selection

    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = (
        "import pytest\n\n"
        "@pytest.mark.parametrize('value', [\n"
        "    pytest.param(1, marks=pytest.mark.xfail(strict=True), "
        "id='expected'),\n"
        "    2,\n"
        "])\n"
        "def test_value(value):\n"
        "    assert value == 2\n"
    )

    result = SandboxRunner().run(test_code, source_path)
    selection = passing_test_selection(test_code, result.test_outcomes)

    assert selection is not None
    assert selection.expected_failure_count == 1
    assert selection.wrong_test_count == 0
    assert selection.passing_test_count == 1
    assert selection.for_test_file("tests/test_generated.py") == (
        "tests/test_generated.py::test_value[expected]",
    )


def test_sandbox_runs_xfail_assertions_for_honest_scoring(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = (
        "import pytest\n\n"
        "@pytest.mark.xfail(strict=True)\n"
        "def test_wrong_xfail():\n"
        "    assert 1 == 2\n"
    )

    result = SandboxRunner().run(test_code, source_path)

    assert result.failed == 1
    assert result.returncode != 0
    assert result.test_outcomes[0].failure_kind == "assertion_failure"


def test_sandbox_enforces_timeout(tmp_path: Path) -> None:
    source_path = tmp_path / "subject.py"
    source_path.write_text("VALUE = 1\n", encoding="utf-8")
    test_code = "import time\n\ndef test_slow():\n    time.sleep(2)\n"

    result = SandboxRunner(timeout_seconds=0.1).run(test_code, source_path)

    assert result.timed_out
    assert result.wall_clock_seconds < 2
    assert result.returncode is None


def test_sandbox_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="Timeout must be a finite positive number"):
        SandboxRunner(timeout_seconds=0)


@pytest.mark.parametrize("timeout_seconds", [float("inf"), float("nan")])
def test_sandbox_rejects_non_finite_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="Timeout must be a finite positive number"):
        SandboxRunner(timeout_seconds=timeout_seconds)


def test_sandbox_requires_existing_source_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        SandboxRunner().run("def test_empty():\n    pass\n", tmp_path / "missing.py")
