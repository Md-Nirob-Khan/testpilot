#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.special_factorial(n=1)
    assert var_0 == 1
    var_1 = testpilot_target_.special_factorial(n=var_0)
    assert var_1 == 1
    var_2 = dict
    testpilot_target_.special_factorial(n=var_2)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.special_factorial(n=-230.28)
