#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_29 = 206
    var_30 = testpilot_target_.below_threshold(l=(), t=var_29)
    assert var_30 is True
    var_16 = 1
    var_17 = testpilot_target_.below_threshold(l=(183.36,), t=var_16)
    assert var_17 is False
    testpilot_target_.below_threshold(l=var_17, t=True)


@pytest.mark.xfail(strict=True)
def test_1():
    var_2 = 1
    var_3 = testpilot_target_.below_threshold(l=(183.36,), t=var_2)
    assert var_3 is False
    testpilot_target_.below_threshold(l=var_3, t=True)


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.below_threshold(l=[], t=-1964)
    var_3 = testpilot_target_.below_threshold(l=[-680.17], t=3)
    assert var_3 is True
    var_4 = -833
    testpilot_target_.below_threshold(l=var_3, t=var_4)
