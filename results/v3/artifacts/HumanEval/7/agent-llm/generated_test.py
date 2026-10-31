import pytest
from testpilot_target import filter_by_substring

def test_filter_by_substring():
    assert filter_by_substring([], 'a') == []
    assert filter_by_substring(['abc', 'bacd', 'cde', 'array'], 'a') == ['abc', 'bacd', 'array']