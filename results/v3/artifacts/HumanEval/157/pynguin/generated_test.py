#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.right_angle_triangle(
        a=True, b=complex(1599.1257, 410.0346981), c=-819
    )
    assert var_0 is False


def test_1():
    var_1 = testpilot_target_.right_angle_triangle(a=-2015, b=True, c=-1643)
    var_5 = testpilot_target_.right_angle_triangle(a=True, b=var_1, c=var_1)
    assert var_5 is False
    var_46 = testpilot_target_.right_angle_triangle(a=var_5, b=var_5, c=var_5)
    assert var_46 is True


@pytest.mark.xfail(strict=True)
def test_2():
    var_1 = testpilot_target_.right_angle_triangle(a=-2015, b=True, c=-1643)
    assert var_1 is False
    var_5 = testpilot_target_.right_angle_triangle(a=False, b=var_1, c=var_1)
    assert var_5 is True
    var_46 = testpilot_target_.right_angle_triangle(a=var_1, b=var_5, c=var_5)
    assert var_46 is True
    var_52 = str
    testpilot_target_.right_angle_triangle(a=var_1, b=var_5, c=var_52)
