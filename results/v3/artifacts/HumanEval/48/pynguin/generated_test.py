#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.is_palindrome(text={})
    assert var_0 is True
    var_1 = "\n    Checks if given string is a palindrome\n    >>> is_palindrome('')\n    True\n    >>> is_palindrome('aba')\n    True\n    >>> is_palindrome('aaaaa')\n    True\n    >>> is_palindrome('zbcd')\n    False\n    "
    var_2 = testpilot_target_.is_palindrome(text=var_1)
    assert var_2 is False
    var_3 = object
    testpilot_target_.is_palindrome(text=var_3)


def test_1():
    lambda *args, **kwargs: 1


def test_2():
    var_7 = testpilot_target_.is_palindrome(text=")W")
    assert var_7 is False
    testpilot_target_.is_palindrome(text="\x0b\x0cp~(\rvj0Q3t(I>")
    var_11 = "+[3a?ShXn6xMFrWFH\r"
    testpilot_target_.is_palindrome(text=var_11)
    var_13 = "I"
    var_14 = testpilot_target_.is_palindrome(text=var_13)
    assert var_14 is True
