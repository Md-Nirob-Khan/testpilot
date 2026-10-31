import pytest
from testpilot_target import move_one_ball

@pytest.mark.parametrize("arr, expected", [
    ([3, 4, 5, 1, 2], True),
    ([3, 5, 4, 1, 2], False),
    ([], True),
    ([1, 2, 3, 4, 5], True),
    ([5, 4, 3, 2, 1], False)
])
def test_move_one_ball(arr, expected):
    assert move_one_ball(arr) == expected