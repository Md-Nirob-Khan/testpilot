#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.move_one_ball(arr=[1622.56, "ZEmOEB"])


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.move_one_ball(arr=-230.28)


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.move_one_ball(arr=(False, -2624.86))
    assert var_0 is True
    testpilot_target_.move_one_ball(arr=var_0)


@pytest.mark.xfail(strict=True)
def test_3():
    var_0 = testpilot_target_.move_one_ball(arr="Y2LG]eR-D")
    assert var_0 is False
    testpilot_target_.move_one_ball(arr=complex(-2158.048962, 1854.0))


@pytest.mark.xfail(strict=True)
def test_4():
    var_1 = testpilot_target_.move_one_ball(arr=set())
    assert var_1 is True
    testpilot_target_.move_one_ball(arr=var_1)
