#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.median(l=[])


@pytest.mark.xfail(strict=True)
def test_1():
    var_1 = testpilot_target_.median(l=[0])
    assert var_1 == 0
    var_26 = testpilot_target_.median(l=b":6")
    assert var_26 == pytest.approx(56.0, abs=0.01, rel=0.01)
    testpilot_target_.median(l=var_1)
