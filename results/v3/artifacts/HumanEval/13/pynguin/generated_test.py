#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = -1129
    var_1 = testpilot_target_.greatest_common_divisor(a=var_0, b={})
    assert var_1 == -1129
    var_2 = 2
    var_3 = testpilot_target_.greatest_common_divisor(a=var_2, b=var_0)
    assert var_3 == -1
    var_4 = 684
    testpilot_target_.greatest_common_divisor(a=var_2, b=var_4)
    var_6 = hash
    var_7 = -353
    testpilot_target_.greatest_common_divisor(a=var_6, b=var_7)


def test_1():
    var_0 = -1801
    var_1 = testpilot_target_.greatest_common_divisor(a=var_0, b=var_0)
    assert var_1 == -1801
