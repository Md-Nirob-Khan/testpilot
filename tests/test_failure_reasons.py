"""Tests for readable wrong-test explanations."""

from pathlib import Path

from testpilot.failure_reasons import collect_wrong_test_reasons, parse_failure_reasons

SOURCE = "def ticket_price(age):\n    if age < 12:\n        return 7\n    return 12\n"
TESTS = (
    "from testpilot_target import ticket_price\n\n"
    "def test_senior():\n    assert ticket_price(64) == 7\n\n"
    "def test_child():\n    assert ticket_price(5) == 7\n\n"
    "def test_boom():\n    raise ValueError('bad')\n"
)


def test_known_answer_reasons_from_real_pytest(tmp_path: Path) -> None:
    """A deliberately wrong assertion is explained in plain words."""
    source = tmp_path / "ticket.py"
    source.write_text(SOURCE, encoding="utf-8")
    reasons = collect_wrong_test_reasons(TESTS, source)
    assert (
        "test_senior: ticket_price(64) returned 12, but the test expected 7"
        in reasons
    )
    assert any(r.startswith("test_boom: ValueError") for r in reasons)
    assert not any(r.startswith("test_child") for r in reasons)


def test_parse_filters_to_named_tests() -> None:
    """Only the requested wrong tests are kept."""
    output = (
        "____ test_a ____\n\nE   assert 1 == 2\n\n"
        "____ test_b ____\n\nE   assert 3 == 4\n"
    )
    assert parse_failure_reasons(output, {"test_b"}) == (
        "test_b: the check `assert 3 == 4` failed",
    )


def test_parse_returns_nothing_for_passing_output() -> None:
    """Output without failure sections gives no reasons."""
    assert parse_failure_reasons("1 passed in 0.01s") == ()
