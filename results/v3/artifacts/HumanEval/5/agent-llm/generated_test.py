import pytest
from testpilot_target import intersperse

def test_intersperse():
    assert intersperse([], 4) == []
    assert intersperse([1, 2, 3], 4) == [1, 4, 2, 4, 3]