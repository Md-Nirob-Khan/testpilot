#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_65 = testpilot_target_.is_nested(
        string="\n    Create a function that takes a string as input which contains only square brackets.\n    The function should return True if and only if there is a valid subsequence of brackets \n    where at least one bracket in the subsequence is nested.\n\n    is_nested('[[]]') ➞ True\n    is_nested('[]]]]]]][[[[[]') ➞ False\n    is_nested('[][]') ➞ False\n    is_nested('[]') ➞ False\n    is_nested('[[][]]') ➞ True\n    is_nested('[[]][[') ➞ True\n    "
    )
    assert var_65 is True
    testpilot_target_.is_nested(string=var_65)


@pytest.mark.xfail(strict=True)
def test_1():
    var_20 = {
        "\n    Create a function that takes a string as input which contains only square brackets.\n    The function should return True if and only if there is a valid subsequence of brackets \n    where at least one bracket in the subsequence is nested.\n\n    is_nested('[[]]') ➞ True\n    is_nested('[]]]]]]][[[[[]') ➞ False\n    is_nested('[][]') ➞ False\n    is_nested('[]') ➞ False\n    is_nested('[[][]]') ➞ True\n    is_nested('[[]][[') ➞ True\n    ": -2066.0,
        "\n    Create a function that takes a string as input which contains only square brackets.\n    The function should return True if and only if there is a valid subsequence of brackets \n    where at least one bracket in the subsequence is nested.\n\n    is_nested('[[]]') ➞ True\n    is_nested('[]]]]]]][[[[[]') ➞ False\n    is_nested('[][]') ➞ False\n    is_nested('[]') ➞ False\n    is_nested('[[][]]') ➞ True\n    is_nested('[[]][[') ➞ True\n    ": -3044,
    }
    testpilot_target_.is_nested(string=var_20)


@pytest.mark.xfail(strict=True)
def test_2():
    var_2 = testpilot_target_.is_nested(string="[")
    assert var_2 is False
    testpilot_target_.is_nested(string=lambda *args, **kwargs: True)
