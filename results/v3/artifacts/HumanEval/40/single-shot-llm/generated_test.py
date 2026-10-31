import pytest

from testpilot_target import triples_sum_to_zero

def test_triples_sum_to_zero():
    assert not triples_sum_to_zero([1, 3, 5, 0])
    assert triples_sum_to_zero([1, 3, -2, 1])
    assert not triples_sum_to_zero([1, 2, 3, 7])
    assert triples_sum_to_zero([2, 4, -5, 3, 9, 7])
    assert not triples_sum_to_zero([1])