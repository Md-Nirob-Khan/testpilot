#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.tri(n=-2111)


@pytest.mark.xfail(strict=True)
def test_1():
    var_7 = testpilot_target_.tri(n=False)
    testpilot_target_.tri(n=var_7)


def test_2():
    testpilot_target_.tri(n=2286)
