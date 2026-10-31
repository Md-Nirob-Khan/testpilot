import pytest
from testpilot_target import do_algebra

def test_do_algebra():
    assert do_algebra(['+', '*', '-'], [2, 3, 4, 5]) == 9
    assert do_algebra(['**', '//'], [2, 3]) == 8
    assert do_algebra(['-', '+'], [10, 5, 3]) == 8
    assert do_algebra(['*', '//'], [4, 2, 1]) == 8
    assert do_algebra(['**', '+'], [2, 3, 4]) == 28