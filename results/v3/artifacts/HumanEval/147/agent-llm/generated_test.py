import pytest
from testpilot_target import get_max_triples

@pytest.mark.parametrize("n, expected", [(5, 1), (10, 3)])
def test_get_max_triples(n, expected):
    assert get_max_triples(n) == expected