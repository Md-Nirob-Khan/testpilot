#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_101 = testpilot_target_.is_simple_power(x=3, n=3)
    assert var_101 is True


def test_1():
    var_101 = testpilot_target_.is_simple_power(x=3, n=3)
    assert var_101 is True
    var_103 = testpilot_target_.is_simple_power(x=var_101, n=var_101)
    assert var_103 is True
    testpilot_target_.is_simple_power(x=-149.91, n=2032.42)


def test_2():
    var_101 = testpilot_target_.is_simple_power(x=3, n=3)
    assert var_101 is True
    var_103 = testpilot_target_.is_simple_power(x=var_101, n=var_101)
    assert var_103 is True


def test_3():
    var_101 = testpilot_target_.is_simple_power(x=3, n=-1141)
    assert var_101 is False
