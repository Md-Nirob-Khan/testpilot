import pytest
from testpilot_target import get_odd_collatz

def test_get_odd_collatz():
    assert get_odd_collatz(5) == [1, 5]
    assert get_odd_collatz(1) == [1]
    assert get_odd_collatz(10) == [1, 5]
    assert get_odd_collatz(15) == [1, 5, 16]
    assert get_odd_collatz(2) == [1]
    assert get_odd_collatz(3) == [1, 3]
    assert get_odd_collatz(4) == [1, 5]
    assert get_odd_collatz(6) == [1, 5, 16]
    assert get_odd_collatz(7) == [1, 7]
    assert get_odd_collatz(8) == [1, 5, 16]
    assert get_odd_collatz(9) == [1, 5, 16]
    assert get_odd_collatz(100) == [1, 5, 16, 8, 4, 2, 1]