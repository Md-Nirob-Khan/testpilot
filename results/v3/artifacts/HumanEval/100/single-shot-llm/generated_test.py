import pytest

def make_a_pile(n):
    """
    Given a positive integer n, you have to make a pile of n levels of stones.
    The first level has n stones.
    The number of stones in the next level is:
        - the next odd number if n is odd.
        - the next even number if n is even.
    Return the number of stones in each level in a list, where element at index
    i represents the number of stones in the level (i+1).

    Examples:
    >>> make_a_pile(3)
    [3, 5, 7]
    """
    return [n + 2*i for i in range(n)]

def test_make_a_pile():
    assert make_a_pile(3) == [3, 5, 7]
    assert make_a_pile(1) == [1]
    assert make_a_pile(2) == [2, 4]
    assert make_a_pile(0) == []
    assert make_a_pile(10) == [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]