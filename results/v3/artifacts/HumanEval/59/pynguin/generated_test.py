#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = -173
    testpilot_target_.largest_prime_factor(n=var_0)
    var_2 = 0
    var_3 = testpilot_target_.largest_prime_factor(n=var_2)
    assert var_3 == 1
    testpilot_target_.largest_prime_factor(n=var_2)
    var_5 = testpilot_target_.largest_prime_factor(n=2)
    assert var_5 == 2
    var_6 = 1216
    var_7 = testpilot_target_.largest_prime_factor(n=var_6)
    var_8 = testpilot_target_.largest_prime_factor(n=var_7)
    assert var_8 == 19


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.largest_prime_factor(n=[])
