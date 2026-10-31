"""Tests that the Streamlit dashboard can render its initial page."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from testpilot.evaluator import MutantExplanation
from testpilot.storage import EngineRun, RunHistory


def test_dashboard_renders_generation_page(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TESTPILOT_DB_PATH", str(tmp_path / "dashboard.sqlite3"))
    app_path = Path(__file__).parents[1] / "app.py"

    app = AppTest.from_file(str(app_path)).run()

    assert not app.exception
    assert any("<h1>Generate &amp; compare</h1>" in m.value for m in app.markdown)
    assert next(radio for radio in app.radio if radio.label == "Workspace").value == (
        "Generate & compare"
    )
    assert "Grade score" in app.selectbox[0].options[0]


def test_history_page_renders_flaky_merge_and_mutant_details(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "dashboard.sqlite3"
    monkeypatch.setenv("TESTPILOT_DB_PATH", str(database_path))
    history = RunHistory(database_path)
    history.save_run(
        "sample.py",
        ["classify"],
        [
            EngineRun(
                function_name="classify",
                engine_name="best-of-merge",
                status="completed",
                test_code="def test_classify():\n    assert True\n",
                flaky_test_names=("test_classify",),
                flaky_run_count=3,
                mutant_explanations=(
                    MutantExplanation(
                        mutant_name="classify_mutant_1",
                        description="A comparison boundary changed.",
                        missing_test_case="Test the equality boundary.",
                        diff="- value > 0\n+ value >= 0",
                    ),
                ),
                merge_selected_test_names=("pynguin:test_classify",),
                merge_mutants_killed=2,
                merge_mutants_available=3,
            )
        ],
    )
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=10)

    workspace = next(radio for radio in app.radio if radio.label == "Workspace")
    workspace.set_value("Run history").run(timeout=10)

    assert not app.exception
    assert any("Flaky tests" in item.value for item in app.warning)
    assert any(
        "Surviving mutants" in item.value
        for item in app.markdown
    )
    assert any(
        "Missing test case" in item.value
        for item in app.markdown
    )
    assert any(
        "Selected tests" in item.value
        for item in app.markdown
    )


def test_experiment_results_page_renders_csv_derived_summary() -> None:
    """Render the final experiment page from its checked-in result CSV."""
    app_path = Path(__file__).parents[1] / "app.py"
    app = AppTest.from_file(str(app_path)).run(timeout=20)

    workspace = next(radio for radio in app.radio if radio.label == "Workspace")
    app = workspace.set_value("Experiment results").run(timeout=20)

    assert not app.exception
    assert any("<h1>Experiment results</h1>" in item.value for item in app.markdown)
    assert any(
        "single-shot suites passed their tests but never called" in item.value
        for item in app.markdown
    )
    assert len(app.dataframe) == 2


def test_currency_labels_zero_cost() -> None:
    """Zero cost is labeled as a local model, or LLM-free for Pynguin."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "dashboard_app", Path(__file__).parents[1] / "app.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._currency(0.0, "agent-llm") == "$0.00 (local model)"
    assert module._currency(0.0, "pynguin") == "$0.00 (no LLM)"
    assert module._currency(None) == "-"


def test_wrong_test_reasons_round_trip_through_history(tmp_path: Path) -> None:
    """Saved wrong-test explanations are restored from SQLite."""
    history = RunHistory(tmp_path / "reasons.sqlite3")
    run_id = history.save_run(
        "s.py",
        ["f"],
        [
            EngineRun(
                function_name="f",
                engine_name="pynguin",
                status="completed",
                wrong_test_count=1,
                wrong_test_reasons=("test_a: f(1) returned 2, but the test expected 3",),
            )
        ],
    )
    stored = history.get_run(run_id).results[0]
    assert stored.wrong_test_reasons == (
        "test_a: f(1) returned 2, but the test expected 3",
    )


def test_history_page_shows_why_test_is_wrong(tmp_path: Path, monkeypatch) -> None:
    """The failing assertion is shown in a dedicated box on the engine tab."""
    database_path = tmp_path / "why.sqlite3"
    monkeypatch.setenv("TESTPILOT_DB_PATH", str(database_path))
    RunHistory(database_path).save_run(
        "s.py",
        ["ticket_price"],
        [
            EngineRun(
                function_name="ticket_price",
                engine_name="single-shot-llm",
                status="completed",
                test_code="def test_a():\n    assert False\n",
                wrong_test_count=1,
                wrong_test_reasons=(
                    "test_a: ticket_price(64) returned 12, but the test expected 7",
                ),
            )
        ],
    )
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run(timeout=10)
    next(r for r in app.radio if r.label == "Workspace").set_value("Run history").run(
        timeout=10
    )
    app = app.run(timeout=10)
    assert not app.exception
    assert any(
        "Why this test is wrong" in m.value and "returned 12" in m.value
        for m in app.markdown
    )
