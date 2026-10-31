#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.do_algebra(operator=[], operand=(1257.06, False, -2439))
    assert var_0 == pytest.approx(1257.06, abs=0.01, rel=0.01)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.do_algebra(
        operator="\n    Given two lists operator, and operand. The first list has basic algebra operations, and \n    the second list is a list of integers. Use the two given lists to build the algebric \n    expression and return the evaluation of this expression.\n\n    The basic algebra operations:\n    Addition ( + ) \n    Subtraction ( - ) \n    Multiplication ( * ) \n    Floor division ( // ) \n    Exponentiation ( ** ) \n\n    Example:\n    operator['+', '*', '-']\n    array = [2, 3, 4, 5]\n    result = 2 + 3 * 4 - 5\n    => result = 9\n\n    Note:\n        The length of operator list is equal to the length of operand list minus one.\n        Operand is a list of of non-negative integers.\n        Operator list has at least one operator, and operand list has at least two operands.\n\n    ",
        operand=b"]Y0RX\x98\xa7\x06\xc5N+\xfcY\x9d",
    )
