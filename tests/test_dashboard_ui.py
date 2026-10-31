"""Tests for dashboard presentation helpers."""

from testpilot.dashboard_ui import (
    ENGINE_COLORS,
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
