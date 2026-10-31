#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.string_to_md5(text=())
    var_1 = testpilot_target_.string_to_md5(text='2bO#Wur-J66A"/@')
    assert var_1 == "389b3467d03b2787f8d79b4eae65e232"
    testpilot_target_.string_to_md5(text=3)
