#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.is_palindrome(string="BUOC\x0cA")
    assert var_0 is False
    var_1 = testpilot_target_.make_palindrome(string=var_0)
    assert var_1 == ""
    var_2 = testpilot_target_.make_palindrome(
        string=" Test if given string is a palindrome :: Test if given string is a palindrome "
    )
    assert (
        var_2
        == " Test if given string is a palindrome :: Test if given string is a palindrome emordnilap a si gnirts nevig fi tseT :: emordnilap a si gnirts nevig fi tseT "
    )


def test_1():
    var_1 = testpilot_target_.make_palindrome(
        string=" Test if given string is a palindrome "
    )
    assert (
        var_1
        == " Test if given string is a palindrome emordnilap a si gnirts nevig fi tseT "
    )
