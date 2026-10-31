#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_49 = testpilot_target_.x_or_y(n=-1613, x=complex(-524.144, 992.01), y=None)
    assert var_49 == (-524.144 + 992.01j)
    testpilot_target_.x_or_y(n=(), x=">.n\x0bgT#7f%jClkF{s", y=947.67)


@pytest.mark.xfail(strict=True)
def test_1():
    var_51 = lambda *args, **kwargs: True
    testpilot_target_.x_or_y(n=True, x=[True], y=var_51)
    testpilot_target_.x_or_y(n=var_51, x=var_51, y=b"\xb4\xdbP\xb5\x08Ei\x16\x7f\xe0")


def test_2():
    var_0 = bool
    testpilot_target_.x_or_y(n=1012, x=[-2545, False, -673.84], y=var_0)


def test_3():
    testpilot_target_.x_or_y(n=2203, x={}, y=b"\x7f0\x0b6M")
