#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.exchange(lst1=[], lst2=[False])
    assert var_0 == "YES"


def test_1():
    var_0 = testpilot_target_.exchange(
        lst1=b"*=6\xbd\xbc\xa7\xc9\xf6\xa3Mq\x00L\x04", lst2=(-1205, 1097.36)
    )
    assert var_0 == "NO"
