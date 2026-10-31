#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.fib(n=[])


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = 2
    var_1 = testpilot_target_.fib(n=var_0)
    assert var_1 == 1
    testpilot_target_.fib(n=var_0)
    var_3 = bytes
    testpilot_target_.fib(n=var_3)
