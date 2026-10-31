#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.car_race_collision(n=-3050.58)
    assert var_0 == pytest.approx(9306038.3364, abs=0.01, rel=0.01)
    var_1 = abs
    testpilot_target_.car_race_collision(n=var_1)
