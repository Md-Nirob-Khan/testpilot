#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.truncate_number(number=-1003.39)
    assert var_0 == pytest.approx(0.6100000000000136, abs=0.01, rel=0.01)
    var_1 = float
    testpilot_target_.truncate_number(number=var_1)
