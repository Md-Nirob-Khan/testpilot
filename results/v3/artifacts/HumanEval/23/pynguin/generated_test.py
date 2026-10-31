#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = " Return length of given string\n    >>> strlen('')\n    0\n    >>> strlen('abc')\n    3\n    "
    var_1 = testpilot_target_.strlen(string=var_0)
    assert var_1 == 88
