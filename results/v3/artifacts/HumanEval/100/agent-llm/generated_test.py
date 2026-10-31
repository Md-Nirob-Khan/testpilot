import pytest
from testpilot_target import make_a_pile

def test_make_a_pile():
    assert make_a_pile(3) == [3, 5, 7]
    assert make_a_pile(1) == [1]
    assert make_a_pile(2) == [2, 4]
    assert make_a_pile(0) == []
    assert make_a_pile(10) == [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]