import pytest
from testpilot_target import hex_key

@pytest.mark.parametrize("num, expected", [
    ("AB", 1),
    ("1077E", 2),
    ("ABED1A33", 4),
    ("123456789ABCDEF0", 6),
    ("2020", 2),
])
def test_hex_key(num, expected):
    assert hex_key(num) == expected