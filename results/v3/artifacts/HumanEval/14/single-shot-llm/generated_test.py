import pytest
from testpilot_target import all_prefixes

def test_all_prefixes():
    assert all_prefixes('abc') == ['a', 'ab', 'abc']
    assert all_prefixes('') == []
    assert all_prefixes('a') == ['a']
    assert all_prefixes('ab') == ['a', 'ab']
    assert all_prefixes('abcde') == ['a', 'ab', 'abc', 'abcd', 'abcde']