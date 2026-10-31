import pytest
from testpilot_target import parse_nested_parens

def test_parse_nested_parens():
    assert parse_nested_parens('(()()) ((())) () ((())()())') == [2, 3, 1, 3]