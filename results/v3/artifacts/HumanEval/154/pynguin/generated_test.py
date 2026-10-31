#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.cycpattern_check(a=[], b=(1257.06, False, -2439))
    assert var_0 is False


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.cycpattern_check(
        a=b"-(\xc9\x07|\x83\x1d\x12\xe5<\xb8q\x97\x94Sk2\xbf", b=b"<\xbci\xde"
    )
    assert var_0 is False
    testpilot_target_.cycpattern_check(a=set(), b=set())


@pytest.mark.xfail(strict=True)
def test_2():
    var_8 = testpilot_target_.cycpattern_check(a=[False, "-8F"], b=[])
    assert var_8 is True
    testpilot_target_.cycpattern_check(a=var_8, b=())
