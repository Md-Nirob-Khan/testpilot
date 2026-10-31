"""Presentation helpers for the Streamlit dashboard: colors, HTML, charts."""

from html import escape
from typing import Any, Sequence

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
html, body, [class*="st-"], .stMarkdown, button, input, textarea {
    font-family: 'Inter', system-ui, sans-serif;
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
        f"<div class='value'>{escape(value)}</div></div>"
    )


def badge_html(kind: str) -> str:
    """Build a status badge; color always accompanies a text label."""
    color, text = BADGE_STYLES[kind]
    return f"<span class='tp-badge' style='--badge:{color}'>{escape(text)}</span>"


def status_badge_kinds(
    status: str,
    error: str | None,
    wrong_test_count: int | float | None,
    does_not_call_target: bool,
) -> list[str]:
    """Choose the status badges that describe one engine result."""
    message = (error or "").lower()
    if "timeout" in message or "timed out" in message:
        return ["timeout"]
    if status != "completed" or error:
        return ["error"]
    kinds = []
    if wrong_test_count:
        kinds.append("wrong")
    if does_not_call_target:
        kinds.append("no-target")
    return kinds or ["passed"]


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
