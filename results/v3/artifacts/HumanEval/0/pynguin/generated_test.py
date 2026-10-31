#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = bool
    var_1 = testpilot_target_.has_close_elements(
        numbers=("S$FbP\\cnhZFv",), threshold=var_0
    )
    assert var_1 is False
    var_2 = 261.34
    var_3 = 3029.15
    var_4 = 1825.61
    var_5 = [var_2, var_2, var_3, var_4, var_2]
    var_6 = testpilot_target_.has_close_elements(numbers=var_5, threshold=var_2)
    assert var_6 is True
    testpilot_target_.has_close_elements(numbers=var_5, threshold=var_6)


def test_1():
    var_0 = bool
    var_1 = testpilot_target_.has_close_elements(
        numbers=("S$FbP\\cnhZFv",), threshold=var_0
    )
    assert var_1 is False
    var_2 = 261.34
    var_3 = 3029.15
    var_4 = 1825.61
    var_5 = [var_2, var_2, var_3, var_4, var_2]
    testpilot_target_.has_close_elements(numbers=set(), threshold=var_4)
    testpilot_target_.has_close_elements(numbers=var_5, threshold=var_4)
    var_12 = testpilot_target_.has_close_elements(numbers=var_5, threshold=var_2)
    assert var_12 is True
    var_13 = -1499.1180458329488
    var_14 = 2762.53
    var_15 = [var_14, var_13, var_14]
    var_16 = testpilot_target_.has_close_elements(numbers=var_15, threshold=var_13)
    assert var_16 is False
    var_17 = -1369.12
    testpilot_target_.has_close_elements(numbers=var_15, threshold=var_17)
