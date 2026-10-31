#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_66 = testpilot_target_.file_name_check(file_name="H+9Hq&h5cc\x0cz\\")
    assert var_66 == "No"


def test_1():
    var_80 = testpilot_target_.file_name_check(file_name="2!`c/Saj.sq")
    assert var_80 == "No"


def test_2():
    var_83 = testpilot_target_.file_name_check(file_name="Yes.dll")
    assert var_83 == "Yes"
