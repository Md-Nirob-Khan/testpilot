#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.largest_divisor(n=False)
    var_1 = 146
    var_2 = testpilot_target_.largest_divisor(n=var_1)
    assert var_2 == 73
    testpilot_target_.largest_divisor(n=var_0)
