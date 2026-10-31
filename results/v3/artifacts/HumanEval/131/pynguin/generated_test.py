#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.digits(n=(183.36,))


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.digits(n=467.31)


@pytest.mark.xfail(strict=True)
def test_2():
    var_46 = testpilot_target_.digits(n=2806)
    assert var_46 == 0
    testpilot_target_.digits(
        n={
            "Given a positive integer n, return the product of the odd digits.\n    Return 0 if all digits are even.\n    For example:\n    digits(1)  == 1\n    digits(4)  == 0\n    digits(235) == 15\n    ": -1215.82
        }
    )


@pytest.mark.xfail(strict=True)
def test_3():
    var_46 = testpilot_target_.digits(n=2547)
    assert var_46 == 35
    testpilot_target_.digits(n=var_46)
    testpilot_target_.digits(n=b"\x81\xe9\x94\xb9\x84\x1f")
