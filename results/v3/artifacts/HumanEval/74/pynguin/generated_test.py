#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.total_match(lst1=[], lst2=(1257.06, False, -2439))


@pytest.mark.xfail(strict=True)
def test_1():
    var_14 = testpilot_target_.total_match(
        lst1="K2KDnrH\x0b!oshj9Bc", lst2="g/Mjkn_\x0b<l}U5QK]}uU"
    )
    assert var_14 == "K2KDnrH\x0b!oshj9Bc"
    testpilot_target_.total_match(lst1=[], lst2=None)


def test_2():
    testpilot_target_.total_match(lst1="(4K`'/>ad\x0bv[\\", lst2=())
