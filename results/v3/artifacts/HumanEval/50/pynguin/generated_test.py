#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = "41C+:dGAW"
    var_1 = testpilot_target_.decode_shift(s=var_0)
    assert var_1 == "czrtiyvpl"
    testpilot_target_.decode_shift(s=var_0)
