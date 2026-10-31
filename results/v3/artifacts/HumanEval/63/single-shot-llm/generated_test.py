import pytest

from testpilot_target import fibfib

def test_fibfib():
    assert fibfib(1) == 0
    assert fibfib(5) == 4
    assert fibfib(8) == 24