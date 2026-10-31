import pytest
from testpilot_target import match_parens

def test_match_parens():
    assert match_parens(['()(', ')']) == 'Yes'
    assert match_parens([')', ')']) == 'No'