import pytest
from testpilot_target import is_nested

def test_is_nested():
    assert is_nested('[[]]') == True
    assert is_nested('[]]]]]]][[[[[]') == False
    assert is_nested('[][]') == False
    assert is_nested('[]') == False
    assert is_nested('[[][]]') == True
    assert is_nested('[[]][[') == True