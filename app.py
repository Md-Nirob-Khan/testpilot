"""Streamlit dashboard for comparing generated test suites."""

import re
import tempfile
from pathlib import Path

import streamlit as st

from testpilot.analyzer import SourceAnalysisError, analyze_source
from testpilot.comparison import ENGINE_NAMES, compare_functions
from testpilot.storage import EngineRun, RunHistory, RunSummary


def main() -> None:
    """Render the generation dashboard and persisted run history."""
    st.set_page_config(page_title="TestPilot", layout="wide")
    st.title("TestPilot")
    st.caption("Generate and honestly compare pytest suites for Python functions.")
    page = st.radio(
        "Page",
        ("Generate & compare", "Run history"),
        horizontal=True,
        label_visibility="collapsed",
    )
    history = RunHistory()
    if page == "Generate & compare":
        _render_generation_page(history)
    else:
        _render_history_page(history)


def _render_generation_page(history: RunHistory) -> None:
    """Collect source and options, then run and persist selected engines."""
    input_mode = st.radio("Python source", ("Paste code", "Upload .py file"))
    source_name: str
    source_code: str
    if input_mode == "Upload .py file":
        uploaded_file = st.file_uploader("Choose a Python file", type=["py"])
        if uploaded_file is None:
            st.info("Upload a .py file to continue.")
            return
        source_name = Path(uploaded_file.name).name
        try:
            source_code = uploaded_file.getvalue().decode("utf-8")
        except UnicodeDecodeError as exc:
            st.error(f"The uploaded file is not valid UTF-8: {exc}")
            return
        st.code(source_code, language="python")
    else:
        source_name = st.text_input("Source filename", "submitted.py")
        source_code = st.text_area(
            "Paste Python source",
            height=260,
            placeholder="def example(value):\n    return value * 2",
        )

    if not source_code.strip():
        return
    try:
        function_infos = analyze_source(
            source_code,
            source_path=Path(source_name or "submitted.py"),
        )
    except SourceAnalysisError as exc:
        st.error(str(exc))
        return
    if not function_infos:
        st.warning("No top-level Python functions were found in this source.")
        return

    with st.form("generation-options"):
        selected_functions = st.multiselect(
            "Functions",
            [function.name for function in function_infos],
            default=[function.name for function in function_infos],
        )
        selected_engines = st.multiselect(
            "Generation engines",
            ENGINE_NAMES,
            default=["Pynguin"],
        )
        submitted = st.form_submit_button(
            "Generate, evaluate, and save run",
            type="primary",
            disabled=not selected_functions or not selected_engines,
        )

    if not submitted:
        return

    functions_by_name = {function.name: function for function in function_infos}
    chosen_functions = [functions_by_name[name] for name in selected_functions]
    with st.spinner("Generating suites and running isolated evaluations..."):
        with tempfile.TemporaryDirectory(prefix="testpilot-dashboard-") as directory:
            source_path = Path(directory) / (Path(source_name).name or "submitted.py")
            source_path.write_text(source_code, encoding="utf-8")
            results = compare_functions(
                source_path,
                chosen_functions,
                selected_engines,
            )
        run_id = history.save_run(source_name, selected_functions, results)

    st.session_state["current_run_id"] = run_id
    st.success(f"Run #{run_id} saved to SQLite history.")
    _render_results(results)


def _render_history_page(history: RunHistory) -> None:
    """Show saved runs and their persisted metrics and generated files."""
    runs = history.list_runs()
    if not runs:
        st.info("No saved runs yet. Generate a comparison to start your history.")
        return
    selected_run = st.selectbox(
        "Saved runs",
        runs,
        format_func=_format_run_summary,
    )
    stored_run = history.get_run(selected_run.run_id)
    st.caption(
        f"Source: {stored_run.summary.source_name} | "
        f"Functions: {', '.join(stored_run.summary.function_names)}"
    )
    _render_results(stored_run.results)


def _render_results(results: tuple[EngineRun, ...] | list[EngineRun]) -> None:
    """Display comparison metrics and download buttons for generated suites."""
    if not results:
        st.warning("This run did not produce any engine results.")
        return

    table_rows = [_table_row(result) for result in results]
    st.subheader("Side-by-side comparison")
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    for index, result in enumerate(results):
        label = f"{result.function_name} | {_display_engine(result.engine_name)}"
        with st.expander(label, expanded=bool(result.error)):
            if result.error:
                st.error(result.error)
            if result.test_code is not None:
                st.code(result.test_code, language="python")
                st.download_button(
                    "Download generated test file",
                    data=result.test_code,
                    file_name=_test_filename(result),
                    mime="text/x-python",
                    key=(
                        f"download-{result.function_name}-"
                        f"{result.engine_name}-{index}"
                    ),
                )


def _table_row(result: EngineRun) -> dict[str, str]:
    """Format one engine result for the comparison table."""
    wrong_tests = "-"
    if result.wrong_test_status is not None:
        count = result.wrong_test_count
        count_text = str(count) if count is not None else "?"
        wrong_tests = f"{count_text} ({_human_status(result.wrong_test_status)})"

    return {
        "Function": result.function_name,
        "Engine": _display_engine(result.engine_name),
        "Line coverage": _percent(result.line_percent),
        "Branch coverage": _percent(result.branch_percent),
        "Mutation score": (
            _percent(result.mutation_score * 100)
            if result.mutation_score is not None
            else "Not scored"
        ),
        "Wrong tests / status": wrong_tests,
        "Time (s)": _number(result.wall_clock_seconds),
        "Cost (USD)": _currency(result.estimated_cost_usd),
        "Run status": result.status,
        "Details": result.error or "",
    }


def _format_run_summary(summary: RunSummary) -> str:
    """Create a concise label for a saved run."""
    return (
        f"#{summary.run_id} | {summary.created_at[:19].replace('T', ' ')} | "
        f"{summary.source_name}"
    )


def _display_engine(engine_name: str) -> str:
    """Map persisted engine identifiers to readable names."""
    return {
        "single-shot-llm": "Single-shot LLM",
        "agent-llm": "Agent LLM",
        "pynguin": "Pynguin",
    }.get(engine_name, engine_name)


def _human_status(status: str) -> str:
    """Clarify correctness status without calling user-code failures wrong tests."""
    return {
        "passed": "passed",
        "wrong_test": "wrong test",
        "needs_human_review": "needs review",
        "timed_out": "timed out",
    }.get(status, status.replace("_", " "))


def _percent(value: float | None) -> str:
    """Format a percentage or show that the measurement is unavailable."""
    return f"{value:.1f}%" if value is not None else "-"


def _number(value: float | None) -> str:
    """Format a numeric metric or show that it is unavailable."""
    return f"{value:.2f}" if value is not None else "-"


def _currency(value: float | None) -> str:
    """Format estimated cost in dollars or show that it is unavailable."""
    return f"${value:.6f}" if value is not None else "-"


def _test_filename(result: EngineRun) -> str:
    """Build a filesystem-safe name for a generated test suite."""
    stem = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        f"{result.function_name}_{result.engine_name}",
    ).strip("_")
    return f"test_{stem or 'generated'}.py"


if __name__ == "__main__":
    main()
