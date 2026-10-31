#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = "00 Input are two strings a and b consisting only of 1s and 0s.\n    Perform binary XOR on these inputs and return result also as a string.\n    >>> string_xor('010', '110')\n    '100'\n    "
    var_1 = "'uDYoL]"
    var_2 = testpilot_target_.string_xor(a=var_0, b=var_1)
    assert var_2 == "1111111"
    testpilot_target_.string_xor(a=-1958.16, b=239.99)
