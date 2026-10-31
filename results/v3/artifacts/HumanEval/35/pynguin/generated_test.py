#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.max_element(l="hX\\&*/E\nU;}#S)")
    assert var_0 == "}"
    var_1 = testpilot_target_.max_element(l=b"EUQ\xe4\x8a\x14#&")
    testpilot_target_.max_element(l=var_1)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.max_element(l=[])
