"""Presentation helpers for the Streamlit dashboard: colors, HTML, charts."""

import math
import re
from html import escape
from typing import Any, Sequence

ENGINE_ORDER = ("single-shot-llm", "agent-llm", "pynguin")

ENGINE_COLORS = {
    "single-shot-llm": "#3B82F6",
    "agent-llm": "#A855F7",
    "pynguin": "#14B8A6",
    "best-of-merge": "#EC4899",
}
ENGINE_ICONS = {
    "single-shot-llm": "⚡",
    "agent-llm": "🤖",
    "pynguin": "🧬",
    "best-of-merge": "🧩",
}
_FALLBACK_COLOR = "#94A3B8"

BADGE_STYLES = {
    "passed": ("#22C55E", "✔ Passed"),
    "wrong": ("#EF4444", "✖ Wrong tests"),
    "no-target": ("#F59E0B", "⚠ Does not call target"),
    "error": ("#94A3B8", "● Error"),
    "timeout": ("#94A3B8", "⏱ Timeout"),
}

STYLESHEET = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
.stApp, .stMarkdown, .stButton button, .stDownloadButton button, input, textarea,
[data-testid="stSidebar"] {
    font-family: 'Inter', system-ui, sans-serif;
}
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded,
[class*="material-symbols"], [class*="MaterialIcon"] {
    font-family: "Material Symbols Rounded", "Material Icons" !important;
}
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }
[data-testid="stSidebar"] { border-right: 1px solid #263449; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
.tp-hero {
    background: linear-gradient(120deg, #1E3A8A 0%, #6D28D9 55%, #0F766E 100%);
    border-radius: 18px; padding: 1.6rem 2rem; margin-bottom: 1.5rem;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
}
.tp-hero .brand { font-size: 0.85rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #DBEAFE; }
.tp-hero .tagline { font-weight: 500; color: #E0E7FF; opacity: 0.9; }
.tp-hero h1 { font-size: 2.2rem; font-weight: 800; color: #FFFFFF; margin: 0.2rem 0;
    padding: 0; }
.tp-hero p { color: #E8EDF5; margin: 0.3rem 0 0; font-size: 1.02rem; }
.tp-card { background: #121D2E; border: 1px solid #29384D; border-top: 4px solid var(--accent);
    border-radius: 14px; padding: 1rem 1.1rem; height: 100%; }
.tp-card.best { box-shadow: 0 0 0 2px var(--accent), 0 6px 22px rgba(0,0,0,.35); }
.tp-card .icon { font-size: 1.2rem; }
.tp-card .value { font-size: 2rem; font-weight: 800; color: #F8FAFC; line-height: 1.15; }
.tp-card .value.long { font-size: 1.15rem; padding: 0.55rem 0; }
.tp-card .label { font-size: 0.78rem; color: #A7B3C5; text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600; }
.tp-best { background: #FACC15; color: #1F1300; font-weight: 800; font-size: 0.7rem;
    border-radius: 999px; padding: 0.15rem 0.6rem; margin-left: 0.4rem;
    vertical-align: middle; }
.tp-engine-head { font-weight: 700; font-size: 1.05rem; color: var(--accent);
    margin: 0.2rem 0 0.5rem; }
.tp-badge { display: inline-block; border-radius: 999px; padding: 0.15rem 0.7rem;
    font-size: 0.78rem; font-weight: 700; margin: 0 0.35rem 0.35rem 0;
    color: #0B1220; background: var(--badge); }
.tp-callout { background: linear-gradient(120deg, rgba(245,158,11,.22), rgba(239,68,68,.18));
    border: 2px solid #F59E0B; border-radius: 18px; padding: 1.5rem 2rem;
    margin: 1.2rem 0; }
.tp-callout .big { font-size: 3.4rem; font-weight: 800; color: #FBBF24; line-height: 1; }
.tp-callout .text { font-size: 1.25rem; font-weight: 600; color: #F8FAFC; margin-top: .4rem; }
.tp-callout .sub { color: #CBD5E1; margin-top: .3rem; }
"""


def engine_color(engine_name: str) -> str:
    """Return the fixed accent color for an engine."""
    return ENGINE_COLORS.get(engine_name, _FALLBACK_COLOR)


def tab_stylesheet(engine_names: Sequence[str]) -> str:
    """Return CSS that colors each engine tab's label and selected underline."""
    rules = []
    for index, name in enumerate(engine_names, start=1):
        color = engine_color(name)
        rules.append(
            f'.tp-tabs-{len(engine_names)} button[data-baseweb="tab"]:nth-of-type({index})'
            f" {{ color: {color}; font-weight: 700; }}"
        )
    return "\n".join(rules)


def hero_html(title: str, description: str) -> str:
    """Build the gradient banner shown at the top of each page."""
    return (
        "<div class='tp-hero'>"
        "<div class='brand'>TestPilot <span class='tagline'>· Test quality, measured.</span></div>"
        f"<h1>{escape(title)}</h1>"
        f"<p>{escape(description)}</p>"
        "</div>"
    )


def metric_card_html(
    label: str,
    value: str,
    icon: str,
    color: str,
    best: bool = False,
) -> str:
    """Build a metric card with an accent border, icon, large value and label."""
    badge = "<span class='tp-best'>★ Best</span>" if best else ""
    return (
        f"<div class='tp-card{' best' if best else ''}' style='--accent:{color}'>"
        f"<div class='label'><span class='icon'>{icon}</span> {escape(label)}{badge}</div>"
        f"<div class='value{' long' if len(value) > 10 else ''}'>{escape(value)}</div></div>"
    )


def badge_html(kind: str) -> str:
    """Build a status badge; color always accompanies a text label."""
    color, text = BADGE_STYLES[kind]
    return f"<span class='tp-badge' style='--badge:{color}'>{escape(text)}</span>"


def classify_failure(error: str, engine_name: str | None = None) -> tuple[str, str]:
    """Map a raw error message to a badge kind and a one-line plain summary."""
    text = error.lower()
    missing = re.search(r"no module named ['\"]([\w.]+)['\"]", error, re.IGNORECASE)
    if "never imported" in text or "no data to report" in text:
        return (
            "no-target",
            "The generated tests never call your function, so coverage and "
            "mutation could not be measured.",
        )
    if missing:
        package = missing.group(1).split(".")[0]
        if engine_name == "pynguin":
            return (
                "error",
                f"Pynguin could not import your code: the package {package} is "
                "missing from the Pynguin environment (.venv-pynguin).",
            )
        return (
            "error",
            f"Your code needs the package {package}, which is not installed "
            "in the environment that ran it.",
        )
    if "timeout" in text or "timed out" in text or re.search(r"exceeded [\d.]+ s", text):
        return ("timeout", "The run exceeded its time limit and was stopped.")
    if "connection" in text and ("refused" in text or "error" in text):
        return ("error", "TestPilot could not reach the LLM provider; check that it is running.")
    first_line = error.strip().splitlines()[0] if error.strip() else "(no details)"
    return ("error", f"The engine failed: {first_line[:140]}")


def status_badge_kinds(
    status: str,
    error: str | None,
    wrong_test_count: int | float | None,
    does_not_call_target: bool,
    engine_name: str | None = None,
) -> list[str]:
    """Choose the status badges that describe one engine result."""
    kinds: list[str] = []
    if error:
        kinds.append(classify_failure(error, engine_name)[0])
    elif status != "completed":
        kinds.append("error")
    if wrong_test_count:
        kinds.append("wrong")
    if does_not_call_target and "no-target" not in kinds:
        kinds.append("no-target")
    return kinds or ["passed"]


def best_flags(values: Sequence[float | None], higher_is_better: bool) -> list[bool]:
    """Flag the best values; flag nothing when fewer than two differ."""
    present = [v for v in values if v is not None]
    if len(present) < 2 or all(math.isclose(v, present[0], abs_tol=1e-12) for v in present):
        return [False] * len(values)
    target = max(present) if higher_is_better else min(present)
    return [v is not None and math.isclose(v, target, abs_tol=1e-12) for v in values]


def ordered_by_engine(items: Sequence[Any], key: Any) -> list[Any]:
    """Sort items so engines always appear as single-shot, agent, Pynguin."""
    def position(item: Any) -> int:
        name = key(item)
        return ENGINE_ORDER.index(name) if name in ENGINE_ORDER else len(ENGINE_ORDER)

    return sorted(items, key=position)


def callout_html(count: int, total: int) -> str:
    """Build the headline callout for single-shot suites that skip the target."""
    return (
        "<div class='tp-callout'>"
        f"<div class='big'>{count} of {total}</div>"
        "<div class='text'>single-shot suites passed their tests but never called "
        "the target function.</div>"
        "<div class='sub'>A passing suite is not evidence of a tested function.</div>"
        "</div>"
    )


def build_bar_figure(
    metrics: Sequence[str],
    values_by_engine: dict[str, Sequence[float | None]],
    maximum: float | None,
    y_title: str,
) -> Any:
    """Build a transparent Plotly grouped bar chart, one colored trace per engine."""
    import plotly.graph_objects as go

    figure = go.Figure()
    for engine_name, values in values_by_engine.items():
        figure.add_bar(
            x=list(metrics),
            y=list(values),
            name=_label_for(engine_name),
            marker={"color": engine_color(engine_name)},
            text=[f"{v:.1f}" if v is not None else "" for v in values],
            textposition="outside",
            cliponaxis=False,
        )
    figure.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": "#E8EDF5", "size": 14},
        height=340,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        legend={"orientation": "h", "y": -0.2, "title": None},
    )
    figure.update_xaxes(showgrid=False, tickfont={"size": 14})
    figure.update_yaxes(
        title=y_title,
        gridcolor="rgba(148,163,184,0.2)",
        range=[0, maximum * 1.15] if maximum else None,
        tickfont={"size": 13},
    )
    return figure


def _label_for(engine_name: str) -> str:
    """Return a readable engine name for chart legends."""
    return {
        "single-shot-llm": "Single-shot LLM",
        "agent-llm": "Agent LLM",
        "pynguin": "Pynguin",
        "best-of-merge": "Best-of merge",
    }.get(engine_name, engine_name)
