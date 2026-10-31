#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.below_zero(operations=[])
    assert var_0 is False
    testpilot_target_.below_zero(operations=var_0)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.below_zero(operations=["X^%Ig\x0c)>.n\x0bgT#"])


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = 0
    var_1 = 432
    var_2 = [var_0, var_0, var_1]
    var_3 = testpilot_target_.below_zero(operations=var_2)
    assert var_3 is False
    testpilot_target_.below_zero(operations=var_2)
    testpilot_target_.below_zero(operations=var_2)
    testpilot_target_.below_zero(operations=var_2)
    var_7 = str
    testpilot_target_.below_zero(operations=var_7)


@pytest.mark.xfail(strict=True)
def test_3():
    var_0 = 0
    var_1 = 0
    var_2 = 346
    var_3 = -3796
    var_4 = 0
    var_5 = [var_0, var_1, var_2, var_3, var_4]
    var_6 = testpilot_target_.below_zero(operations=var_5)
    assert var_6 is True
    testpilot_target_.below_zero(operations=var_5)
    testpilot_target_.below_zero(operations=var_5)
    testpilot_target_.below_zero(operations=var_5)
    testpilot_target_.below_zero(operations=var_5)
    var_11 = -4342
    var_12 = 0
    var_13 = -4765
    var_14 = [var_11, var_11, var_12, var_13]
    var_15 = testpilot_target_.below_zero(operations=var_14)
    assert var_15 is True
    testpilot_target_.below_zero(operations=var_14)
    testpilot_target_.below_zero(operations=var_5)
    testpilot_target_.below_zero(operations=var_5)
    testpilot_target_.below_zero(operations=var_14)
    testpilot_target_.below_zero(operations=var_14)
    testpilot_target_.below_zero(operations=complex(1895.55, 1791.5479296))
