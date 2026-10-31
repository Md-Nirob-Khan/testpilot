import pytest

from testpilot_target import pairs_sum_to_zero

def test_pairs_sum_to_zero():
    assert not pairs_sum_to_zero([1, 3, 5, 0])
    assert not pairs_sum_to_zero([1, 3, -2, 1])
    assert not pairs_sum_to_zero([1, 2, 3, 7])
    assert pairs_sum_to_zero([2, 4, -5, 3, 5, 7])
    assert not pairs_sum_to_zero([1])