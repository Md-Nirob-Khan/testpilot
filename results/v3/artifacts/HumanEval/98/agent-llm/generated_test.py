import pytest

def test_count_upper():
    from testpilot_target import count_upper
    assert count_upper('aBCdEf') == 1
    assert count_upper('abcdefg') == 0
    assert count_upper('dBBE') == 0