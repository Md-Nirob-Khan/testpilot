#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_3 = testpilot_target_.check_dict_case(dict={})
    assert var_3 is False


def test_1():
    var_6 = testpilot_target_.check_dict_case(
        dict={
            '\n    Given a dictionary, return True if all keys are strings in lower \n    case or all keys are strings in upper case, else return False.\n    The function should return False is the given dictionary is empty.\n    Examples:\n    check_dict_case({"a":"apple", "b":"banana"}) should return True.\n    check_dict_case({"a":"apple", "A":"banana", "B":"banana"}) should return False.\n    check_dict_case({"a":"apple", 8:"banana", "a":"apple"}) should return False.\n    check_dict_case({"Name":"John", "Age":"36", "City":"Houston"}) should return False.\n    check_dict_case({"STATE":"NC", "ZIP":"12345" }) should return True.\n    ': 1882,
            "mixed": "mixed,mixed,lower,upper",
            "mixed": "W!38YeIZXl",
        }
    )
    assert var_6 is False


def test_2():
    var_3 = testpilot_target_.check_dict_case(
        dict={"start": "start,mixed,mixed", "lower": 3057}
    )
    assert var_3 is True


def test_3():
    var_0 = testpilot_target_.check_dict_case(
        dict={
            "upper": False,
            '\n    Given a dictionary, return True if all keys are strings in lower \n    case or all keys are strings in upper case, else return False.\n    The function should return False is the given dictionary is empty.\n    Examples:\n    check_dict_case({"a":"apple", "b":"banana"}) should return True.\n    check_dict_case({"a":"apple", "A":"banana", "B":"banana"}) should return False.\n    check_dict_case({"a":"apple", 8:"banana", "a":"apple"}) should return False.\n    check_dict_case({"Name":"John", "Age":"36", "City":"Houston"}) should return False.\n    check_dict_case({"STATE":"NC", "ZIP":"12345" }) should return True.\n    ': 467.31,
            "mixed": -225.56,
        }
    )
    assert var_0 is False
