#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.check_if_last_char_is_a_letter(
        txt='\n    Create a function that returns True if the last character\n    of a given string is an alphabetical character and is not\n    a part of a word, and False otherwise.\n    Note: "word" is a group of characters separated by space.\n\n    Examples:\n    check_if_last_char_is_a_letter("apple pie") ➞ False\n    check_if_last_char_is_a_letter("apple pi e") ➞ True\n    check_if_last_char_is_a_letter("apple pi e ") ➞ False\n    check_if_last_char_is_a_letter("") ➞ False \n      '
    )
    assert var_0 is False


def test_1():
    var_0 = testpilot_target_.check_if_last_char_is_a_letter(txt="_Eg [")
    assert var_0 is False


def test_2():
    var_30 = testpilot_target_.check_if_last_char_is_a_letter(txt="X")
    assert var_30 is True


def test_3():
    var_0 = testpilot_target_.check_if_last_char_is_a_letter(txt="}")
    assert var_0 is False
