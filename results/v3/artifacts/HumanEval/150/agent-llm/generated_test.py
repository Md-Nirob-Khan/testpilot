import pytest
from testpilot_target import x_or_y

def test_x_or_y():
    assert x_or_y(7, 34, 12) == 34
    assert x_or_y(15, 8, 5) == 5
    assert x_or_y(2, 10, 20) == 10
    assert x_or_y(1, 5, 10) == 10
    assert x_or_y(4, 1, 2) == 2