#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.is_sorted(
        lst={
            -2995,
            "\n    Given a list of numbers, return whether or not they are sorted\n    in ascending order. If list has more than 1 duplicate of the same\n    number, return False. Assume no negative numbers and only integers.\n\n    Examples\n    is_sorted([5]) ➞ True\n    is_sorted([1, 2, 3, 4, 5]) ➞ True\n    is_sorted([1, 3, 2, 4, 5]) ➞ False\n    is_sorted([1, 2, 3, 4, 5, 6]) ➞ True\n    is_sorted([1, 2, 3, 4, 5, 6, 7]) ➞ True\n    is_sorted([1, 3, 2, 4, 5, 6, 7]) ➞ False\n    is_sorted([1, 2, 2, 3, 3, 4]) ➞ True\n    is_sorted([1, 2, 2, 2, 3, 4]) ➞ False\n    ",
        }
    )


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.is_sorted(lst="Y2LG]eR-D")
    assert var_0 is False
    testpilot_target_.is_sorted(lst=complex(-636.619444, -3477.49))


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.is_sorted(lst={"*\\J9O 5T2W9E,S,P"})
    assert var_0 is True
    testpilot_target_.is_sorted(lst=complex(-950.9926, -1220.0))


@pytest.mark.xfail(strict=True)
def test_3():
    var_0 = testpilot_target_.is_sorted(lst={"*\\J9O 5T2W9E,S,P"})
    assert var_0 is True
    var_1 = testpilot_target_.is_sorted(
        lst="\n    Given a list of numbers, return whether or not they are sorted\n    in ascending order. If list has more than 1 duplicate of the same\n    number, return False. Assume no negative numbers and only integers.\n\n    Examples\n    is_sorted([5]) ➞ True\n    is_sorted([1, 2, 3, 4, 5]) ➞ True\n    is_sorted([1, 3, 2, 4, 5]) ➞ False\n    is_sorted([1, 2, 3, 4, 5, 6]) ➞ True\n    is_sorted([1, 2, 3, 4, 5, 6, 7]) ➞ True\n    is_sorted([1, 3, 2, 4, 5, 6, 7]) ➞ False\n    is_sorted([1, 2, 2, 3, 3, 4]) ➞ True\n    is_sorted([1, 2, 2, 2, 3, 4]) ➞ False\n    "
    )
    assert var_1 is False
    testpilot_target_.is_sorted(lst=var_1)
