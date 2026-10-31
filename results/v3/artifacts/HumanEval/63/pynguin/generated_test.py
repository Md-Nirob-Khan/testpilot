#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.fibfib(n=-1052)


@pytest.mark.xfail(strict=True)
def test_1():
    var_2 = 0
    var_3 = testpilot_target_.fibfib(n=var_2)
    assert var_3 == 0
    testpilot_target_.fibfib(n=var_2)
    testpilot_target_.fibfib(n=0)
    var_6 = 1216
    testpilot_target_.fibfib(n=var_6)


@pytest.mark.xfail(strict=True)
def test_2():
    var_2 = 17
    var_13 = testpilot_target_.fibfib(n=var_2)
    assert var_13 == 5768
    var_14 = 0
    testpilot_target_.fibfib(n=var_14)
    testpilot_target_.fibfib(n=var_14)
    testpilot_target_.fibfib(n=0)
    var_18 = 1216
    testpilot_target_.fibfib(n=var_18)
