#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.prod_signs(arr=0)
    var_2 = dict
    testpilot_target_.prod_signs(arr=var_2)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.prod_signs(arr=-230.28)


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.prod_signs(arr=(False, -2624.86))
    assert var_0 == pytest.approx(0.0, abs=0.01, rel=0.01)
    testpilot_target_.prod_signs(arr="yV$iT")
