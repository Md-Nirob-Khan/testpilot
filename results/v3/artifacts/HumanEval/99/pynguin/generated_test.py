#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_14 = testpilot_target_.closest_integer(value="0")
    assert var_14 == 0


def test_1():
    var_3 = testpilot_target_.closest_integer(value=".5")
    assert var_3 == 1


def test_2():
    var_0 = testpilot_target_.closest_integer(value="2.0")
    assert var_0 == 2
