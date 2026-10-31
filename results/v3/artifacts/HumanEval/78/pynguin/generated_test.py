#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.hex_key(num="#Xyo")
    assert var_0 == 0


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.hex_key(num=())
    assert var_0 == 0
    var_1 = testpilot_target_.hex_key(num='2bO#Wur-J66A"/@')
    assert var_1 == 1
    testpilot_target_.hex_key(num=0)
