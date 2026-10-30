"""Tests that the Streamlit dashboard can render its initial page."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_generation_page(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TESTPILOT_DB_PATH", str(tmp_path / "dashboard.sqlite3"))
    app_path = Path(__file__).parents[1] / "app.py"

    app = AppTest.from_file(str(app_path)).run()

    assert not app.exception
    assert app.title[0].value == "TestPilot"
    assert app.radio[0].value == "Generate & compare"
