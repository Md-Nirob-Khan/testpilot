#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.minSubArraySum(nums=(False, -2624.86))
    assert var_0 == pytest.approx(-2624.86, abs=0.01, rel=0.01)
    testpilot_target_.minSubArraySum(nums="yV$iT")


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.minSubArraySum(nums="Y2LG]eR-D")


def test_2():
    var_0 = testpilot_target_.minSubArraySum(
        nums=b"\x16\x97l\x08\x07\x177;\x81\x9a\x06\x8f2\xb7\xa6\xb3\x8bk"
    )
    assert var_0 == 6


@pytest.mark.xfail(strict=True)
def test_3():
    testpilot_target_.minSubArraySum(nums=-230.28)
