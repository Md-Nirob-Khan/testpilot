#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_44 = testpilot_target_.monotonic(
        l=b"\xd2\xfd]\x8a\xd2\xc1\n\xc2\xb8p\x8b7\xfdl\x1a\xbc\xd4\xa7"
    )
    assert var_44 is False


def test_1():
    var_0 = testpilot_target_.monotonic(l=[])
    assert var_0 is True


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.monotonic(l=[3971, 2719.08, 959])
    assert var_0 is True
    var_18 = testpilot_target_.monotonic(l={})
    assert var_18 is False
    testpilot_target_.monotonic(l=-1)
