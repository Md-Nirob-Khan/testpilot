#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = 0
    var_1 = testpilot_target_.change_base(x=var_0, base=var_0)
    assert var_1 == ""
    var_2 = 624
    var_3 = 0
    testpilot_target_.change_base(x=var_2, base=var_3)


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = 2
    testpilot_target_.change_base(x=var_0, base=None)


def test_2():
    -3051


def test_3():
    var_0 = 3
    var_1 = testpilot_target_.change_base(x=var_0, base=var_0)
    assert var_1 == "10"
    var_2 = 2
    testpilot_target_.change_base(x=var_2, base=var_0)
