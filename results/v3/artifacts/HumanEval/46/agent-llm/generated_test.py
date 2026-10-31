import pytest

from testpilot_target import fib4

def test_fib4():
    assert fib4(5) == 4
    assert fib4(6) == 8
    assert fib4(7) == 14