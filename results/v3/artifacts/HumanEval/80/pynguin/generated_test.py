#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_1 = testpilot_target_.is_happy(
        s="e You are given a string s.\n    Your task is to check if the string is happy or not.\n    A string is happy if its length is at least 3 and every 3 consecutive letters are distinct\n    For example:\n    is_happy(a) => False\n    is_happy(aa) => False\n    is_happy(abcd) => True\n    is_happy(aabb) => False\n    is_happy(adb) => True\n    is_happy(xyy) => False\n    "
    )
    assert var_1 is False


def test_1():
    var_1 = testpilot_target_.is_happy(s="v562/.$z^svT")
    assert var_1 is True
    var_24 = testpilot_target_.is_happy(s={"8": False})
    assert var_24 is False


def test_2():
    var_1 = testpilot_target_.is_happy(s="89(C=;cs@")
    assert var_1 is True


def test_3():
    var_1 = testpilot_target_.is_happy(s="H+9Hq&h5cc\x0cz\\")
    assert var_1 is False
    var_22 = testpilot_target_.is_happy(s="``9qixT")
    assert var_22 is False
