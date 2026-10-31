#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = -8
    testpilot_target_.intersperse(numbers=None, delimeter=var_0)
    var_2 = 3982
    testpilot_target_.intersperse(numbers=var_0, delimeter=var_2)


def test_1():
    testpilot_target_.intersperse(numbers=(False, 1121.46), delimeter=2)
