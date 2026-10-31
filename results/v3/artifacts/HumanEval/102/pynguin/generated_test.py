#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_32 = testpilot_target_.choose_num(x=-314, y=True)
    assert var_32 == 0


def test_1():
    var_34 = testpilot_target_.choose_num(x=856, y=True)
    assert var_34 == -1
    var_33 = testpilot_target_.choose_num(x=var_34, y=var_34)
    assert var_33 == -1


@pytest.mark.xfail(strict=True)
def test_2():
    var_32 = testpilot_target_.choose_num(x=-314, y=True)
    assert var_32 == 0
    var_34 = testpilot_target_.choose_num(x=var_32, y=var_32)
    assert var_34 == 0
    var_35 = set
    testpilot_target_.choose_num(x=var_35, y=False)
