#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.rounded_avg(n=[], m=(1257.06, False, -2439))


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.rounded_avg(n=409.47, m=-1179)
    assert var_0 == -1
    testpilot_target_.rounded_avg(n=None, m=var_0)


@pytest.mark.xfail(strict=True)
def test_2():
    var_32 = testpilot_target_.rounded_avg(n=-3491, m=False)
    assert var_32 == "-0b11011010010"
    testpilot_target_.rounded_avg(n=str, m=lambda *args, **kwargs: 3139)
