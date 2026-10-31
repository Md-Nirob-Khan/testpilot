"""Streamlit dashboard for comparing generated test suites."""

import os
import re
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Callable

import streamlit as st
from dotenv import load_dotenv

from testpilot.analyzer import SourceAnalysisError, analyze_source
from testpilot.comparison import ENGINE_NAMES, compare_functions
from testpilot.dashboard_ui import (
    STYLESHEET,
    badge_html,
    build_bar_figure,
    callout_html,
    engine_color,
    hero_html,
    metric_card_html,
    status_badge_kinds,
    tab_stylesheet,
    ENGINE_ICONS,
    best_flags,
    classify_failure,
    ordered_by_engine,
)
from testpilot.engines import AgentEngine
from testpilot.engines.llm_engine import target_usage_issue
from testpilot.llm import LLMProvider, create_provider
from testpilot.storage import EngineRun, RunHistory, RunSummary

_SAMPLES = {
    "Grade score - thresholds and boundaries": """def grade(score: float) -> str:
    if not 0 <= score <= 100:
        raise ValueError("score must be between 0 and 100")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"
""",
    "Clamp value - lower and upper bounds": """def clamp(value: float, lower: float, upper: float) -> float:
    if lower > upper:
        raise ValueError("lower must not exceed upper")
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value
""",
    "Shipping cost - free-shipping threshold": """def shipping_cost(total: float, expedited: bool = False) -> float:
    if total < 0:
        raise ValueError("total must be non-negative")
    if total >= 50:
        return 12.0 if expedited else 0.0
    return 20.0 if expedited else 5.0
""",
    "Classify integer - negative, zero, positive": """def classify(value: int) -> str:
    if value < 0:
        return "negative"
    if value == 0:
        return "zero"
    return "positive"
""",
}

_ENGINE_LABELS = {
    "single-shot-llm": "Single-shot LLM",
    "agent-llm": "Agent LLM",
    "pynguin": "Pynguin",
    "best-of-merge": "Best-of merge",
}


def main() -> None:
    """Render the generation, run-history, and experiment-results pages."""
    st.set_page_config(
        page_title="TestPilot | Test quality, measured",
        layout="wide",
    )
    _inject_styles()
    st.sidebar.markdown("## TestPilot")
    st.sidebar.caption("Test quality, measured.")
    page = st.sidebar.radio(
        "Workspace",
        ("Generate & compare", "Experiment results", "Run history"),
        label_visibility="collapsed",
    )
    history = RunHistory()
    if page == "Generate & compare":
        _render_generation_page(history)
    elif page == "Experiment results":
        _render_experiment_page()
    else:
        _render_history_page(history)


def _render_generation_page(history: RunHistory) -> None:
    """Collect source and options, then run and persist selected engines."""
    _render_page_heading(
        "Generate & compare",
        "Compare three independent test-generation approaches on the same function.",
    )
    selected_engines, provider_factory, agent_rounds = _render_run_settings()

    input_mode = st.radio(
        "Source",
        ("Built-in sample", "Paste Python", "Upload .py file"),
        horizontal=True,
    )
    source_name: str
    if input_mode == "Built-in sample":
        if "source_code" not in st.session_state:
            st.session_state.source_code = next(iter(_SAMPLES.values()))
        sample_name = st.selectbox(
            "Choose a branch-and-boundary example",
            tuple(_SAMPLES),
            key="sample_name",
            on_change=_load_selected_sample,
        )
        source_name = _sample_filename(sample_name)
        source_code = st.text_area(
            "Python source",
            height=270,
            key="source_code",
            help="The sample is ready to run; edit it here if you want to explore.",
        )
    elif input_mode == "Upload .py file":
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
        with st.expander("Preview source", expanded=False):
            st.code(source_code, language="python", width="stretch")
    else:
        source_name = st.text_input("Source filename", "submitted.py")
        source_code = st.text_area(
            "Paste Python source",
            height=270,
            key="pasted_source",
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

    selected_functions = st.multiselect(
        "Functions to test",
        [function.name for function in function_infos],
        default=[function.name for function in function_infos],
    )
    run_clicked = st.button(
        "Generate, evaluate & compare",
        type="primary",
        disabled=not selected_functions or not selected_engines,
        width="content",
    )
    if not run_clicked:
        return

    functions_by_name = {function.name: function for function in function_infos}
    chosen_functions = [functions_by_name[name] for name in selected_functions]
    with st.spinner("Generating suites and running isolated evaluations..."):
        with tempfile.TemporaryDirectory(prefix="testpilot-dashboard-") as directory:
            source_path = Path(directory) / (Path(source_name).name or "submitted.py")
            source_path.write_text(source_code, encoding="utf-8")
            factories = {}
            if "Agent LLM" in selected_engines:
                factories["Agent LLM"] = lambda: AgentEngine(
                    provider_factory(),
                    max_rounds=agent_rounds,
                )
            results = compare_functions(
                source_path,
                chosen_functions,
                selected_engines,
                engine_factories=factories,
                provider_factory=provider_factory,
            )
        run_id = history.save_run(source_name, selected_functions, results)

    st.session_state["current_run_id"] = run_id
    st.success(f"Run #{run_id} saved to SQLite history.")
    _render_results(results)


def _render_run_settings() -> tuple[list[str], Callable[[], LLMProvider], int]:
    """Render engine, model, and agent-round controls in the sidebar."""
    load_dotenv()
    st.sidebar.markdown("### Run settings")
    selected_engines = st.sidebar.multiselect(
        "Engines",
        ENGINE_NAMES,
        default=list(ENGINE_NAMES),
    )
    provider_name = st.sidebar.selectbox(
        "LLM provider",
        ("ollama", "anthropic"),
        index=0 if os.getenv("TESTPILOT_LLM_PROVIDER", "ollama") == "ollama" else 1,
        disabled=not any(
            engine in selected_engines for engine in ("Single-shot LLM", "Agent LLM")
        ),
    )
    default_model = os.getenv(
        "OLLAMA_MODEL" if provider_name == "ollama" else "ANTHROPIC_MODEL",
        "llama3.1" if provider_name == "ollama" else "claude-haiku-5-5",
    )
    model_name = st.sidebar.text_input("Model", value=default_model)
    agent_rounds = st.sidebar.selectbox(
        "Agent maximum rounds",
        (1, 2, 3, 4, 5),
        index=2,
        disabled="Agent LLM" not in selected_engines,
    )
    st.sidebar.caption(
        "Generated suites run in timeout-bounded subprocesses. "
        "The agent setting controls its maximum iteration count."
    )

    def provider_factory() -> LLMProvider:
        provider = create_provider(provider_name)
        return replace(provider, model=model_name.strip())

    return selected_engines, provider_factory, agent_rounds


def _load_selected_sample() -> None:
    """Load the selected built-in source into the editable sample field."""
    sample_name = st.session_state.sample_name
    st.session_state.source_code = _SAMPLES[sample_name]


def _render_history_page(history: RunHistory) -> None:
    """Show saved runs and their persisted metrics and generated files."""
    _render_page_heading(
        "Run history",
        "Revisit saved comparisons, generated suites, and quality checks.",
    )
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
        f"Source: {stored_run.summary.source_name}  |  "
        f"Functions: {', '.join(stored_run.summary.function_names)}"
    )
    _render_results(stored_run.results)


def _render_results(results: tuple[EngineRun, ...] | list[EngineRun]) -> None:
    """Render per-function scorecards, comparison charts, and engine tabs."""
    if not results:
        st.warning("This run did not produce any engine results.")
        return

    st.markdown("## Comparison")
    function_names = list(dict.fromkeys(result.function_name for result in results))
    for function_name in function_names:
        function_results = [
            result for result in results if result.function_name == function_name
        ]
        st.markdown(f"### `{function_name}`")
        engine_results = ordered_by_engine(
            [
                result
                for result in function_results
                if result.engine_name != "best-of-merge"
            ],
            lambda result: result.engine_name,
        )
        _render_engine_scorecards(engine_results)
        _render_engine_chart(engine_results)
        tabs_results = [result for result in engine_results if result.test_code is not None]
        if tabs_results:
            st.markdown(
                f"<style>{tab_stylesheet([r.engine_name for r in tabs_results])}</style>",
                unsafe_allow_html=True,
            )
            tabs = st.tabs(
                [
                    f"{ENGINE_ICONS.get(result.engine_name, '🧪')} "
                    f"{_ENGINE_LABELS.get(result.engine_name, result.engine_name)}"
                    for result in tabs_results
                ]
            )
            for index, (tab, result) in enumerate(zip(tabs, tabs_results)):
                with tab:
                    _render_suite_tab(result, index)
        merge_results = [
            result
            for result in function_results
            if result.engine_name == "best-of-merge"
        ]
        for result in merge_results:
            _render_merge_result(result)


def _render_engine_scorecards(results: list[EngineRun]) -> None:
    """Show metric cards per engine with a Best badge on each winning metric."""
    if not results:
        return
    mutation_percent = [
        result.mutation_score * 100 if result.mutation_score is not None else None
        for result in results
    ]
    flags = {
        "line": best_flags([r.line_percent for r in results], True),
        "branch": best_flags([r.branch_percent for r in results], True),
        "mutation": best_flags(mutation_percent, True),
        "wrong": best_flags([r.wrong_test_count for r in results], False),
        "time": best_flags([r.wall_clock_seconds for r in results], False),
        "cost": best_flags([r.estimated_cost_usd for r in results], False),
    }
    columns = st.columns(len(results))
    for index, (column, result) in enumerate(zip(columns, results)):
        with column:
            color = engine_color(result.engine_name)
            icon = ENGINE_ICONS.get(result.engine_name, "🧪")
            label = _ENGINE_LABELS.get(result.engine_name, result.engine_name)
            target_issue = (
                target_usage_issue(result.test_code, result.function_name)
                if result.test_code is not None
                else None
            )
            kinds = status_badge_kinds(
                result.status,
                result.error,
                result.wrong_test_count,
                bool(target_issue),
                result.engine_name,
            )
            st.markdown(
                f"<div class='tp-engine-head' style='--accent:{color}'>"
                f"{icon} {label}</div>"
                + "".join(badge_html(kind) for kind in kinds),
                unsafe_allow_html=True,
            )
            _render_error(result)
            cards = [
                ("Line coverage", _percent(result.line_percent), "📏", flags["line"]),
                (
                    "Branch coverage",
                    _percent(result.branch_percent),
                    "🔀",
                    flags["branch"],
                ),
                (
                    "Mutation score",
                    _percent(mutation_percent[index]),
                    "🧬",
                    flags["mutation"],
                ),
                (
                    "Wrong tests",
                    _number(result.wrong_test_count),
                    "❌",
                    flags["wrong"],
                ),
                (
                    "Calls target",
                    "No" if target_issue else "Yes" if result.test_code else "N/A",
                    "🎯",
                    [False] * len(results),
                ),
                (
                    "Time",
                    _seconds(result.wall_clock_seconds),
                    "⏱",
                    flags["time"],
                ),
                (
                    "Cost",
                    _currency(result.estimated_cost_usd, result.engine_name),
                    "💲",
                    flags["cost"],
                ),
            ]
            for row_start in range(0, len(cards), 2):
                row = st.columns(2)
                for cell, (card_label, value, card_icon, card_flags) in zip(
                    row, cards[row_start : row_start + 2]
                ):
                    cell.markdown(
                        metric_card_html(
                            card_label, value, card_icon, color, card_flags[index]
                        ),
                        unsafe_allow_html=True,
                    )


def _render_error(result: EngineRun) -> None:
    """Show a plain-English cause with the raw error in a collapsed expander."""
    if not result.error:
        return
    _, summary = classify_failure(result.error, result.engine_name)
    st.markdown(summary)
    with st.expander("Technical details"):
        st.code(result.error, language="text", width="stretch")


def _render_engine_chart(results: list[EngineRun]) -> None:
    """Compare line, branch, and mutation percentages across engines."""
    chart_rows = [
        {
            "Engine": _ENGINE_LABELS.get(result.engine_name, result.engine_name),
            "Line coverage": result.line_percent,
            "Branch coverage": result.branch_percent,
            "Mutation score": (
                result.mutation_score * 100
                if result.mutation_score is not None
                else None
            ),
        }
        for result in results
        if result.engine_name != "best-of-merge"
    ]
    if chart_rows:
        _render_bar_chart(
            chart_rows,
            ("Line coverage", "Branch coverage", "Mutation score"),
            maximum=100,
        )


def _render_suite_tab(result: EngineRun, index: int) -> None:
    """Show generated code, download, correctness, stability, and explanations."""
    st.markdown(
        "".join(
            badge_html(kind)
            for kind in status_badge_kinds(
                result.status,
                result.error,
                result.wrong_test_count,
                False,
                result.engine_name,
            )
        ),
        unsafe_allow_html=True,
    )
    _render_error(result)
    if result.test_code is not None:
        st.code(
            result.test_code,
            language="python",
            line_numbers=True,
            width="stretch",
        )
        st.download_button(
            "Download generated test file",
            data=result.test_code,
            file_name=_test_filename(result),
            mime="text/x-python",
            key=f"download-{result.function_name}-{result.engine_name}-{index}",
            width="stretch",
        )
    if result.flaky_run_count is not None:
        _render_flaky_result(result)
    _render_mutant_explanations(result)


def _render_merge_result(result: EngineRun) -> None:
    """Present best-of merge outcome, selected tests, and stability clearly."""
    st.markdown("#### Best-of merge")
    with st.container(border=True):
        if result.error:
            _render_error(result)
        else:
            st.success("Merged passing tests into a smaller suite.")
            st.write(
                f"**Mutation score:** {_percent(result.mutation_score * 100 if result.mutation_score is not None else None)}"
                f"  |  **Coverage:** {_percent(result.line_percent)} line / "
                f"{_percent(result.branch_percent)} branch"
            )
        if result.merge_selected_test_names:
            st.write("**Selected tests**")
            st.write(", ".join(result.merge_selected_test_names))
            st.caption(
                f"Mutants killed by selected cases: "
                f"{result.merge_mutants_killed}/{result.merge_mutants_available}"
            )
        if result.flaky_run_count is not None:
            _render_flaky_result(result)
        _render_mutant_explanations(result)
        if result.test_code is not None:
            st.code(
                result.test_code,
                language="python",
                line_numbers=True,
                width="stretch",
            )
            st.download_button(
                "Download merged test suite",
                data=result.test_code,
                file_name=_test_filename(result),
                mime="text/x-python",
                key=f"download-merge-{result.function_name}",
                width="stretch",
            )


def _render_flaky_result(result: EngineRun) -> None:
    """Show repeated-run stability and timeout details."""
    if result.flaky_test_names:
        st.warning("Flaky tests: " + ", ".join(result.flaky_test_names))
    elif result.flaky_run_count and not (
        result.flaky_timed_out_runs or result.flaky_inconclusive_runs
    ):
        st.success(f"Stable across {result.flaky_run_count} repeated runs.")
    elif result.flaky_run_count:
        st.info("Flakiness could not be determined for every run.")
    if result.flaky_timed_out_runs:
        st.warning(
            "Flakiness was inconclusive for timed-out runs: "
            + ", ".join(str(run) for run in result.flaky_timed_out_runs)
        )
    if result.flaky_inconclusive_runs:
        st.warning(
            "No test outcomes were available for runs: "
            + ", ".join(str(run) for run in result.flaky_inconclusive_runs)
        )


def _render_mutant_explanations(result: EngineRun) -> None:
    """Show each surviving mutant and a targeted missing-test suggestion."""
    if not result.mutant_explanations:
        return
    st.markdown("**Surviving mutants**")
    for explanation in result.mutant_explanations:
        with st.expander(explanation.mutant_name):
            st.write(f"**What changed:** {explanation.description}")
            st.write(f"**Missing test case:** {explanation.missing_test_case}")
            if explanation.diff:
                st.code(explanation.diff, language="diff", width="stretch")


def _render_experiment_page() -> None:
    """Present data-derived metrics for the final 164-function experiment."""
    from testpilot.dashboard_summary import load_experiment_dashboard_summary

    _render_page_heading(
        "Experiment results",
        "Final HumanEval run - three engines - paired, CSV-derived analysis.",
    )
    csv_path = (
        Path(__file__).resolve().parent
        / "results"
        / "v3"
        / "humaneval_full_164_rescored.csv"
    )
    try:
        summary = load_experiment_dashboard_summary(csv_path)
    except (OSError, ValueError, ImportError) as exc:
        st.error(f"Could not load experiment results: {exc}")
        return

    st.caption(
        f"Source: `{csv_path.relative_to(Path(__file__).resolve().parent)}`  |  "
        f"{summary.task_count} functions in the CSV  |  "
        f"{summary.paired_function_count} complete paired functions"
    )
    engines = ordered_by_engine(summary.engines, lambda e: e.engine_name)
    flags = {
        "line": best_flags([e.line_coverage for e in engines], True),
        "branch": best_flags([e.branch_coverage for e in engines], True),
        "mutation": best_flags([e.mutation_score for e in engines], True),
        "wrong": best_flags([e.average_wrong_tests for e in engines], False),
        "time": best_flags([e.average_time_seconds for e in engines], False),
        "cost": best_flags([e.average_cost_usd for e in engines], False),
    }
    st.markdown(
        callout_html(
            summary.single_shot_passed_without_target, summary.task_count
        ),
        unsafe_allow_html=True,
    )
    metric_columns = st.columns(len(engines))
    for index, (column, engine) in enumerate(zip(metric_columns, engines)):
        color = engine_color(engine.engine_name)
        with column:
            st.markdown(
                f"<div class='tp-engine-head' style='--accent:{color}'>"
                f"{ENGINE_ICONS[engine.engine_name]} "
                f"{_ENGINE_LABELS[engine.engine_name]}</div>",
                unsafe_allow_html=True,
            )
            for label, value, icon, key in (
                ("Line coverage", _percent(engine.line_coverage), "📏", "line"),
                ("Branch coverage", _percent(engine.branch_coverage), "🔀", "branch"),
                (
                    "Mutation score",
                    _percent(
                        engine.mutation_score * 100
                        if engine.mutation_score is not None
                        else None
                    ),
                    "🧬",
                    "mutation",
                ),
                (
                    "Average wrong tests",
                    _decimal(engine.average_wrong_tests),
                    "❌",
                    "wrong",
                ),
                ("Average time", _seconds(engine.average_time_seconds), "⏱", "time"),
                (
                    "Average cost",
                    _currency(engine.average_cost_usd, engine.engine_name),
                    "💲",
                    "cost",
                ),
            ):
                st.markdown(
                    metric_card_html(label, value, icon, color, flags[key][index]),
                    unsafe_allow_html=True,
                )
            st.caption(
                f"Based on {engine.paired_functions} shared complete-case functions."
            )

    mutation_rows = [
        {
            "Engine": _ENGINE_LABELS[engine.engine_name],
            "Mutation score (%)": (
                engine.mutation_score * 100
                if engine.mutation_score is not None
                else None
            ),
        }
        for engine in engines
    ]
    coverage_rows = [
        {
            "Engine": _ENGINE_LABELS[engine.engine_name],
            "Line coverage (%)": engine.line_coverage,
            "Branch coverage (%)": engine.branch_coverage,
        }
        for engine in engines
    ]
    time_rows = [
        {
            "Engine": _ENGINE_LABELS[engine.engine_name],
            "Average time (s)": engine.average_time_seconds,
        }
        for engine in engines
    ]
    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.markdown("### Mutation score")
        _render_bar_chart(
            mutation_rows,
            ("Mutation score (%)",),
            maximum=100,
        )
    with chart_columns[1]:
        st.markdown("### Coverage")
        _render_bar_chart(
            coverage_rows,
            ("Line coverage (%)", "Branch coverage (%)"),
            maximum=100,
        )
    st.markdown("### Average runtime")
    _render_bar_chart(
        time_rows,
        ("Average time (s)",),
        maximum=None,
    )

    st.markdown("### Failure breakdown")
    failure_rows = [
        {
            "Engine": _ENGINE_LABELS[engine.engine_name],
            "Timeout rows": engine.timeout_rows,
            "Wrong test cases": engine.wrong_test_cases,
            "does_not_call_target": engine.does_not_call_target_rows,
            "no_scorable_tests": engine.no_scorable_tests_rows,
            "Mutation errors": engine.mutation_error_rows,
        }
        for engine in engines
    ]
    st.dataframe(failure_rows, width="stretch", hide_index=True)
    st.caption(
        "Wrong tests are summed test cases; other failure columns count result rows. "
        "Failure categories may overlap."
    )

    st.markdown("### Paired Wilcoxon signed-rank tests")
    wilcoxon_rows = [
        {
            "Engine pair": (
                f"{_ENGINE_LABELS[test.engine_a]} vs "
                f"{_ENGINE_LABELS[test.engine_b]}"
            ),
            "Paired functions": test.functions_included,
            "p-value": (
                f"{test.p_value:.6g}" if test.p_value is not None else "Unavailable"
            ),
        }
        for test in summary.wilcoxon_tests
    ]
    st.dataframe(wilcoxon_rows, width="stretch", hide_index=True)
    st.caption("Two-sided tests use each engine pair's shared functions with mutation scores.")


def _render_bar_chart(
    rows: list[dict[str, float | str | None]],
    metrics: tuple[str, ...],
    maximum: float | None,
) -> None:
    """Render a transparent Plotly chart with one fixed color per engine."""
    label_to_name = {label: name for name, label in _ENGINE_LABELS.items()}
    values_by_engine = {
        label_to_name.get(str(row["Engine"]), str(row["Engine"])): [
            row.get(metric) for metric in metrics
        ]
        for row in rows
    }
    numbers = [
        float(value)
        for values in values_by_engine.values()
        for value in values
        if value is not None
    ]
    if not numbers:
        st.info("No complete metrics are available to chart.")
        return
    figure = build_bar_figure(
        [metric.split(" (")[0] for metric in metrics],
        values_by_engine,
        maximum or max(numbers),
        "Percent" if maximum else metrics[0],
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _render_page_heading(title: str, subtitle: str) -> None:
    """Render the gradient hero banner for the current page."""
    st.markdown(hero_html(title, subtitle), unsafe_allow_html=True)


def _inject_styles() -> None:
    """Apply the dashboard font, spacing, cards, badges, and banner styles."""
    st.markdown(f"<style>{STYLESHEET}</style>", unsafe_allow_html=True)


def _format_run_summary(summary: RunSummary) -> str:
    """Create a concise label for a saved run."""
    return (
        f"#{summary.run_id} | {summary.created_at[:19].replace('T', ' ')} | "
        f"{summary.source_name}"
    )


def _percent(value: float | None) -> str:
    """Format a percentage or show that the measurement is unavailable."""
    return f"{value:.1f}%" if value is not None else "-"


def _number(value: float | int | None) -> str:
    """Format a number or show that the measurement is unavailable."""
    return f"{value:.0f}" if value is not None else "-"


def _decimal(value: float | None) -> str:
    """Format a decimal metric or show that the measurement is unavailable."""
    return f"{value:.2f}" if value is not None else "-"


def _seconds(value: float | None) -> str:
    """Format elapsed time in seconds."""
    return f"{value:.2f} s" if value is not None else "-"


def _currency(value: float | None, engine_name: str | None = None) -> str:
    """Format estimated cost, labeling zero cost as local or LLM-free."""
    if value is None:
        return "-"
    if value == 0:
        return "$0.00 (no LLM)" if engine_name == "pynguin" else "$0.00 (local model)"
    return f"${value:.6f}"


def _sample_filename(sample_name: str) -> str:
    """Build a stable source filename from a display label."""
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", sample_name.split(" - ", 1)[0])
    return f"{stem.lower() or 'sample'}.py"


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
