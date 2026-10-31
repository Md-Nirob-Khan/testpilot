#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_4 = testpilot_target_.is_multiply_prime(a=True)
    assert var_4 is False
    testpilot_target_.is_multiply_prime(a=None)
