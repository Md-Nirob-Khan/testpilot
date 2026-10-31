import pytest
from testpilot_target import solve

@pytest.mark.parametrize("N, expected", [
    (1000, "1"),
    (150, "110"),
    (147, "1100"),
])
def test_solve(N, expected):
    assert solve(N) == expected