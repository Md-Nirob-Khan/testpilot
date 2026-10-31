import pytest
from testpilot_target import is_simple_power

@pytest.mark.parametrize("x, n, expected", [
    (1, 4, True),
    (2, 2, True),
    (8, 2, True),
    (3, 2, False),
    (3, 1, False),
    (5, 3, False),
])
def test_is_simple_power(x, n, expected):
    assert is_simple_power(x, n) == expected