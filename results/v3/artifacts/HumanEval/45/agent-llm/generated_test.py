import pytest

from testpilot_target import triangle_area

def test_triangle_area():
    assert triangle_area(5, 3) == 7.5
    assert triangle_area(0, 0) == 0
    assert triangle_area(10, 5) == 25
    assert triangle_area(7.5, 4.5) == 18.75