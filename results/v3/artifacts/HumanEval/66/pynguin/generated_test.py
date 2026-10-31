#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_17 = testpilot_target_.digitSum(s="eBTkW0}}x#")
    assert var_17 == 237
    testpilot_target_.digitSum(
        s=b"\x16\x97l\x08\x07\x177;\x81\x9a\x06\x8f2\xb7\xa6\xb3\x8bk"
    )


@pytest.mark.xfail(strict=True)
def test_1():
    var_25 = testpilot_target_.digitSum(s="")
    assert var_25 == 0
    testpilot_target_.digitSum(s=var_25)
