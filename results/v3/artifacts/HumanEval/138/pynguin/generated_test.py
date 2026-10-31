#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.is_equal_to_sum_even


@pytest.mark.xfail(strict=True)
def test_1():
    var_3 = testpilot_target_.is_equal_to_sum_even(n=False)
    assert var_3 is False
    var_42 = int
    testpilot_target_.is_equal_to_sum_even(n=var_42)


@pytest.mark.xfail(strict=True)
def test_2():
    var_2 = testpilot_target_.is_equal_to_sum_even(n=2259)
    assert var_2 is False
    testpilot_target_.is_equal_to_sum_even(n=b"\xbe\xdfNk\xc9\xe3T_")
