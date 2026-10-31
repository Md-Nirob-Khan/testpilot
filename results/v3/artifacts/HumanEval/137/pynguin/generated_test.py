#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_29 = testpilot_target_.compare_one(a=546.81, b=1440.63)
    assert var_29 == pytest.approx(1440.63, abs=0.01, rel=0.01)
    var_30 = lambda *args, **kwargs: [False]
    testpilot_target_.compare_one(a=False, b=var_30)


@pytest.mark.xfail(strict=True)
def test_1():
    var_29 = testpilot_target_.compare_one(a=546.81, b=1440.63)
    assert var_29 == pytest.approx(1440.63, abs=0.01, rel=0.01)
    testpilot_target_.compare_one(a="K.@9%wMs%PJI", b=False)


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.compare_one(a=None, b=",,")


def test_3():
    testpilot_target_.compare_one(a=False, b=False)


@pytest.mark.xfail(strict=True)
def test_4():
    var_0 = testpilot_target_.compare_one(a=True, b=-111.61)
    assert var_0 is True
    var_1 = list
    testpilot_target_.compare_one(a=var_1, b=())
