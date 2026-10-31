import pytest
from testpilot_target import concatenate

def test_concatenate_empty():
    assert concatenate([]) == ''

def test_concatenate_single():
    assert concatenate(['a']) == 'a'

def test_concatenate_multiple():
    assert concatenate(['a', 'b', 'c']) == 'abc'