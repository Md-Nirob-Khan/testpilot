#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.specialFilter(nums=[-3248.44, True])
    assert var_0 == 0


def test_1():
    var_0 = testpilot_target_.specialFilter(
        nums=b"\x16\x97l\x08\x07\x177;\x81\x9a\x06\x8f2\xb7\xa6\xb3\x8bk"
    )
    assert var_0 == 9
