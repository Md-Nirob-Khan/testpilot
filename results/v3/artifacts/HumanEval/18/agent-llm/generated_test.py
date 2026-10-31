import pytest
from testpilot_target import how_many_times

def test_how_many_times():
    assert how_many_times('', 'a') == 0
    assert how_many_times('aaa', 'a') == 3
    assert how_many_times('aaaa', 'aa') == 3