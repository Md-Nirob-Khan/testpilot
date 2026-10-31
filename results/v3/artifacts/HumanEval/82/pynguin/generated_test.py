#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_3 = testpilot_target_.prime_length(
        string={
            -2995,
            "Write a function that takes a string and returns True if the string\n    length is a prime number or False otherwise\n    Examples\n    prime_length('Hello') == True\n    prime_length('abcdcba') == True\n    prime_length('kittens') == True\n    prime_length('orange') == False\n    ",
        }
    )
    assert var_3 is True
    var_10 = testpilot_target_.prime_length(string="eBTkW0}}x#")
    assert var_10 is False
    testpilot_target_.prime_length(string=b"=\x0e=\xe0\x91\xf2\x14\x15\xbb|")
    var_42 = testpilot_target_.prime_length(string={})
    assert var_42 is False
    testpilot_target_.prime_length(string=complex(-759.19939, 3150.922791))


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.prime_length(string={"*\\J9O 5T2W9E,S,P"})
    assert var_0 is False
    testpilot_target_.prime_length(string=complex(-950.9926, -1220.0))


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.prime_length(string="Y2LG]eR-D")
    assert var_0 is False
    testpilot_target_.prime_length(string=complex(-636.619444, -3477.49))
