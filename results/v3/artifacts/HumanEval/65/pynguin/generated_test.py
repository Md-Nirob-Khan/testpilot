#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.circular_shift(
        x=b"]eP\xa6G?\xf5\x1d\x06\xbc/\x7f\x84c\xe9\x8f\x1e", shift=622.08
    )
    assert var_0 == "'e1x\\f8x\\9ex\\c48x\\f7x\\/cbx\\60x\\d1x\\5fx\\?G6ax\\Pe]'b"
    testpilot_target_.circular_shift(x=2748, shift=complex(-1040.221, -57.28))


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.circular_shift(x=[], shift=(1257.06, False, -2439))


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.circular_shift(x=int, shift=2)
    assert var_0 == "'><class 'int"
    testpilot_target_.circular_shift(x=(False, '.3{`J++i+o"'), shift=var_0)
