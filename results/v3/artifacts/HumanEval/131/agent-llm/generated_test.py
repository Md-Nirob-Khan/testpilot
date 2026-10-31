import pytest
from testpilot_target import digits

def test_digits():
    assert digits(1) == 1
    assert digits(4) == 0
    assert digits(235) == 15
    assert digits(2468) == 0
    assert digits(13579) == 945
    assert digits(0) == 0
    assert digits(111) == 111
    assert digits(222) == 0
    assert digits(333) == 27
    assert digits(444) == 0
    assert digits(555) == 15
    assert digits(666) == 0
    assert digits(777) == 243
    assert digits(888) == 0
    assert digits(999) == 729