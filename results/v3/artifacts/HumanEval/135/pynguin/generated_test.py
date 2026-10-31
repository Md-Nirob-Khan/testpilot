#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.can_arrange(arr={"*\\J9O 5T2W9E,S,P"})
    assert var_0 == -1
    testpilot_target_.can_arrange(arr=1)


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.can_arrange(arr="Y2LG]eR-D")
    assert var_0 == 7
    testpilot_target_.can_arrange(arr=complex(-2158.048962, 1854.0))


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.can_arrange(arr=-230.28)
