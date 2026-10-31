import pytest
from testpilot_target import will_it_fly

def test_will_it_fly():
    assert will_it_fly([1, 2], 5) == False
    assert will_it_fly([3, 2, 3], 1) == False
    assert will_it_fly([3, 2, 3], 9) == True
    assert will_it_fly([3], 5) == True