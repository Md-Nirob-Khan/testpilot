import pytest

from testpilot_target import special_factorial

def test_special_factorial():
    assert special_factorial(4) == 288
    assert special_factorial(1) == 1
    assert special_factorial(0) == 1
    assert special_factorial(5) == 34560