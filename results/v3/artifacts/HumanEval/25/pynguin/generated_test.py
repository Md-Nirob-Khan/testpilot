#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = 1
    testpilot_target_.factorize(n=var_0)


def test_1():
    var_2 = 0
    testpilot_target_.factorize(n=var_2)


def test_2():
    testpilot_target_.factorize(n=1703)


@pytest.mark.xfail(strict=True)
def test_3():
    testpilot_target_.factorize(
        n=" Return list of prime factors of given integer in the order from smallest to largest.\n    Each of the factors should be listed number of times corresponding to how many times it appeares in factorization.\n    Input number should be equal to the product of all factors\n    >>> factorize(8)\n    [2, 2, 2]\n    >>> factorize(25)\n    [5, 5]\n    >>> factorize(70)\n    [2, 5, 7]\n    "
    )
