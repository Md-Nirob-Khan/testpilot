#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.any_int(x=complex(643.0, 1534.7841), y={"tfgP"}, z=bytes)
    assert var_0 is False
    var_2 = testpilot_target_.any_int(x=var_0, y=var_0, z=True)
    assert var_2 is False


def test_1():
    var_0 = testpilot_target_.any_int(x=False, y=b"\x86\x8d\xfe", z=[])
    assert var_0 is False
    var_26 = testpilot_target_.any_int(x=var_0, y=True, z=var_0)
    assert var_26 is False


def test_2():
    var_0 = testpilot_target_.any_int(x=0, y=2587, z=complex)
    assert var_0 is False
    var_25 = testpilot_target_.any_int(x=True, y=var_0, z=var_0)
    assert var_25 is False


def test_3():
    var_0 = testpilot_target_.any_int(x=bool, y=str, z=(True, -2862.03))
    assert var_0 is False
    var_26 = testpilot_target_.any_int(x=True, y=var_0, z=var_0)
    assert var_26 is False
    var_30 = testpilot_target_.any_int(x=var_26, y=var_26, z=var_0)
    var_31 = testpilot_target_.any_int(x=var_30, y=var_30, z=var_26)
    assert var_31 is True


def test_4():
    var_0 = testpilot_target_.any_int(x=set(), y=False, z=None)
    assert var_0 is False
    var_25 = testpilot_target_.any_int(x=False, y=True, z=-1)
    assert var_25 is True
    var_26 = complex
    testpilot_target_.any_int(x=var_25, y=var_26, z=var_26)
