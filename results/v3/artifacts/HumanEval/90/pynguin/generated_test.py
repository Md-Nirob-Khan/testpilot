#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.next_smallest(lst="Y2LG]eR-D")
    assert var_0 == "2"
    testpilot_target_.next_smallest(lst=complex(-2158.048962, 1854.0))


def test_1():
    testpilot_target_.next_smallest(lst={"*\\J9O 5T2W9E,S,P"})


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.next_smallest(lst=-230.28)
