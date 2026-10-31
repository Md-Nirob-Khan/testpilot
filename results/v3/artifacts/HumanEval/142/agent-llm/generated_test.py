import pytest
from testpilot_target import sum_squares

def test_sum_squares():
    assert sum_squares([1,2,3]) == 6
    assert sum_squares([]) == 0
    assert sum_squares([-1,-5,2,-1,-5]) == -126