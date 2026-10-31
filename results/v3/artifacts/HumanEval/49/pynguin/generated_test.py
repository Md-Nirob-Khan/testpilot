#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = -1433
    var_1 = testpilot_target_.modp(n=1, p=var_0)
    assert var_1 == -1431


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = 3
    testpilot_target_.modp(n=var_0, p={False})


def test_2():
    lambda *args, **kwargs: [False, 559, 4371.58]
