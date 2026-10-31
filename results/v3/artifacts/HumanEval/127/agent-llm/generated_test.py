import pytest
from testpilot_target import intersection

@pytest.mark.parametrize("interval1, interval2, expected", [
    ((1, 2), (2, 3), "NO"),
    ((-1, 1), (0, 4), "NO"),
    ((-3, -1), (-5, 5), "YES"),
])
def test_intersection(interval1, interval2, expected):
    assert intersection(interval1, interval2) == expected