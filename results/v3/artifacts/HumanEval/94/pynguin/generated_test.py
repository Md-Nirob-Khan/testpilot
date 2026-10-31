#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_17 = testpilot_target_.skjkasdkd(lst=b"\xf48\xfd\xa7")
    assert var_17 == 14


def test_1():
    var_3 = testpilot_target_.skjkasdkd(
        lst=b"\xcc\x94O\x9c\r\xe7W\x88\xc7\x02xt\x83\xe7x\x92\xbbT"
    )
    assert var_3 == 19


def test_2():
    var_3 = testpilot_target_.skjkasdkd(
        lst=b"\xcc\x94O\x9c\r\xe7W\x88\xc7\x02xt\x83\xe7x\x92\xbbT"
    )
    assert var_3 == 19
    var_8 = testpilot_target_.skjkasdkd(lst=set())
    assert var_8 == 0
