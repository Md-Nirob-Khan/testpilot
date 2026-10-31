"""Tests for dashboard presentation helpers."""

from testpilot.dashboard_ui import (
    ENGINE_COLORS,
    STYLESHEET,
    best_flags,
    classify_failure,
    ordered_by_engine,
    badge_html,
    build_bar_figure,
    callout_html,
    hero_html,
    metric_card_html,
    status_badge_kinds,
)


def test_engine_colors_are_distinct() -> None:
    """Each engine has its own fixed color."""
    assert len(set(ENGINE_COLORS.values())) == len(ENGINE_COLORS)


def test_status_badge_kinds_cover_each_meaning() -> None:
    """Badge kinds follow the documented status meanings."""
    assert status_badge_kinds("completed", None, 0, False) == ["passed"]
    assert status_badge_kinds("completed", None, 2, False) == ["wrong"]
    assert status_badge_kinds("completed", None, 0, True) == ["no-target"]
    assert status_badge_kinds("failed", "Timed out", None, False) == ["timeout"]
    assert status_badge_kinds("failed", "boom", None, False) == ["error"]


def test_badge_always_has_text_label() -> None:
    """Badges carry words, not only color."""
    assert "Passed" in badge_html("passed")
    assert "Wrong tests" in badge_html("wrong")


def test_hero_escapes_and_includes_tagline() -> None:
    """The hero shows the tagline and escapes page text."""
    html = hero_html("A<b>", "desc")
    assert "Test quality, measured." in html
    assert "A&lt;b&gt;" in html


def test_metric_card_best_badge() -> None:
    """Only the best card carries the Best badge."""
    assert "Best" in metric_card_html("x", "1", "i", "#fff", best=True)
    assert "Best" not in metric_card_html("x", "1", "i", "#fff")


def test_callout_states_counts() -> None:
    """The callout reports the supplied counts."""
    assert "73 of 164" in callout_html(73, 164)


def test_bar_figure_uses_engine_colors() -> None:
    """Traces use the engine colors and a transparent background."""
    figure = build_bar_figure(
        ["Line"], {"pynguin": [50.0], "agent-llm": [80.0]}, 100, "Percent"
    )
    assert figure.data[0].marker.color == ENGINE_COLORS["pynguin"]
    assert figure.data[1].marker.color == ENGINE_COLORS["agent-llm"]
    assert figure.layout.paper_bgcolor == "rgba(0,0,0,0)"


def test_best_flags_direction() -> None:
    """Highest wins for coverage-like metrics; lowest wins for cost-like ones."""
    assert best_flags([37.8, 85.3, 51.2], True) == [False, True, False]
    assert best_flags([0.30, 0.28, 0.0], False) == [False, False, True]
    assert best_flags([17.9, 38.8, 6.7], False) == [False, False, True]


def test_best_flags_none_on_tie_or_single_value() -> None:
    """All-equal values and lone values earn no badge; missing values are skipped."""
    assert best_flags([0.0, 0.0, 0.0], False) == [False, False, False]
    assert best_flags([None, 5.0, None], True) == [False, False, False]
    assert best_flags([None, 5.0, 3.0], True) == [False, True, False]


def test_best_flags_shared_best_both_flagged() -> None:
    """Engines tied for best are both flagged when others differ."""
    assert best_flags([0.0, 0.0, 2.0], False) == [True, True, False]


def test_classify_pynguin_missing_package_is_error_not_timeout() -> None:
    """A missing package in Pynguin explains the cause and is not a timeout."""
    kind, summary = classify_failure(
        "RuntimeError: Pynguin exited: No module named 'numpy'", "pynguin"
    )
    assert kind == "error"
    assert summary == (
        "Pynguin could not import your code: the package numpy is missing from "
        "the Pynguin environment (.venv-pynguin)."
    )


def test_classify_never_imported_is_no_target() -> None:
    """Coverage's never-imported warning maps to the amber no-target badge."""
    kind, summary = classify_failure(
        "Coverage: RuntimeError: Module testpilot_target was never imported."
    )
    assert kind == "no-target"
    assert "never call your function" in summary


def test_classify_timeout_and_generic() -> None:
    """Timeouts and unknown failures get distinct badges and short summaries."""
    assert classify_failure("TimeoutError: mutmut run exceeded 300 seconds")[0] == "timeout"
    kind, summary = classify_failure("ValueError: boom\nTraceback...")
    assert kind == "error" and summary == "The engine failed: ValueError: boom"


def test_status_badge_uses_classification() -> None:
    """The badge kind follows the real cause of the error."""
    assert status_badge_kinds(
        "error", "Pynguin exited: No module named 'numpy'", None, False, "pynguin"
    ) == ["error"]
    assert status_badge_kinds(
        "error", "Module testpilot_target was never imported", None, False
    ) == ["no-target"]


def test_ordered_by_engine_is_canonical() -> None:
    """Engines are always ordered single-shot, agent, Pynguin."""
    names = ["pynguin", "single-shot-llm", "agent-llm"]
    assert ordered_by_engine(names, lambda n: n) == [
        "single-shot-llm",
        "agent-llm",
        "pynguin",
    ]


def test_stylesheet_keeps_material_icon_font() -> None:
    """Icon elements keep their own font instead of Inter."""
    assert "Material Symbols Rounded" in STYLESHEET
    assert '[class*="st-"]' not in STYLESHEET
