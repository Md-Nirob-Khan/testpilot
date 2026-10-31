#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.common(l1={}, l2=b"\xd3\xb4\xb2\x9a\n7\xd5\xdbS%")


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.common(l1="ex\\!&>E/N;O.eI", l2=-2580.58)


def test_2():
    var_11 = [False]
    testpilot_target_.common(l1=var_11, l2=var_11)
    testpilot_target_.common(
        l1=var_11,
        l2="Return sorted unique common elements for two lists.\n    >>> common([1, 4, 3, 34, 653, 2, 5], [5, 7, 1, 5, 9, 653, 121])\n    [1, 5, 653]\n    >>> common([5, 3, 2, 8], [3, 2])\n    [2, 3]\n\n    ",
    )
