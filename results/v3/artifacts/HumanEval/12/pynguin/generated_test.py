#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.longest(strings=[])
    var_8 = testpilot_target_.longest(strings="GJ`WyDwtf}oEf\t'\r_")
    assert var_8 == "G"


def test_1():
    var_0 = testpilot_target_.longest(strings=["JMSr$", 'fXe%h"\rK{A'])
    assert var_0 == 'fXe%h"\rK{A'
