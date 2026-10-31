#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = -19
    var_1 = testpilot_target_.fizz_buzz(n=var_0)
    assert var_1 == 0


def test_1():
    var_0 = 1674
    var_1 = testpilot_target_.fizz_buzz(n=var_0)
    assert var_1 == 68


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.fizz_buzz(n=(True,))
