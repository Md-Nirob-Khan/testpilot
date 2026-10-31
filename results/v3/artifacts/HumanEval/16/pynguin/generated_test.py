#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = " Given a string, find out how many distinct characters (regardless of case) does it consist of\n    >>> count_distinct_characters('xyzXYZ')\n    3\n    >>> count_distinct_characters('Jerry')\n    4\n    "
    var_1 = testpilot_target_.count_distinct_characters(string=var_0)
    assert var_1 == 32
