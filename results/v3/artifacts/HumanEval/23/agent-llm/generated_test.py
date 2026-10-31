import pytest

from testpilot_target import strlen

def test_strlen():
    assert strlen('') == 0
    assert strlen('abc') == 3