#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.sum_squares(lst=(False, -2624.86))
    assert var_0 == 6885376
    testpilot_target_.sum_squares(lst="yV$iT")


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.sum_squares(lst="Y2LG]eR-D")


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.sum_squares(lst=-230.28)
