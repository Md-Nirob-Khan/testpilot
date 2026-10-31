#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_5 = testpilot_target_.triangle_area(a=1121, b=True, c=False)
    assert var_5 == -1


def test_1():
    var_0 = testpilot_target_.triangle_area(a=219, b=False, c=True)
    assert var_0 == -1
    testpilot_target_.triangle_area(a=var_0, b=var_0, c=var_0)


def test_2():
    var_11 = testpilot_target_.triangle_area(a=131.81, b=635, c=1)
    assert var_11 == -1


@pytest.mark.xfail(strict=True)
def test_3():
    var_0 = True
    var_11 = testpilot_target_.triangle_area(a=True, b=var_0, c=var_0)
    assert var_11 == pytest.approx(0.43, abs=0.01, rel=0.01)
    testpilot_target_.triangle_area(a=var_11, b=b"\x100Ph\xd4];\x1c\xe7\xae", c=var_0)
