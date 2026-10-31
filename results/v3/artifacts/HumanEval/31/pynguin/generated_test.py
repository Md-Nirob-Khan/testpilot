#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_3 = testpilot_target_.is_prime(n=2720)
    assert var_3 is False


def test_1():
    var_3 = testpilot_target_.is_prime(n=2720)
    assert var_3 is False
    var_55 = testpilot_target_.is_prime(n=True)
    assert var_55 is False


@pytest.mark.xfail(strict=True)
def test_2():
    var_3 = testpilot_target_.is_prime(n=1231)
    assert var_3 is True
    testpilot_target_.is_prime(n=list)
