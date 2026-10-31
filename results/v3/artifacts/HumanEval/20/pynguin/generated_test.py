#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.find_closest_elements(numbers=b"\xf6O\x1b\x94\x06\xed")
    var_1 = var_0[0]
    assert var_1 == 237
    var_3 = -732.65
    var_4 = 2826.13
    var_5 = 2105.34
    var_6 = [var_3, var_4, var_5]
    var_7 = testpilot_target_.find_closest_elements(numbers=var_6)
    var_8 = var_7[0]
    assert var_8 == pytest.approx(2105.34, abs=0.01, rel=0.01)
