#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_6 = " Find how many times a given substring can be found in the original string. Count overlaping cases.\n    >>> how_many_times('', 'a')\n    0\n    >>> how_many_times('aaa', 'a')\n    3\n    >>> how_many_times('aaaa', 'aa')\n    3\n    "
    var_7 = testpilot_target_.how_many_times(string=".SD+<7; c", substring=var_6)
    assert var_7 == 0


@pytest.mark.xfail(strict=True)
def test_1():
    var_1 = testpilot_target_.how_many_times(
        string=" Find how many times a given substring can be found in the original string. Count overlaping cases.\n    >>> how_many_times('', 'a')\n    0\n    >>> how_many_times('aaa', 'a')\n    3\n    >>> how_many_times('aaaa', 'aa')\n    3\n     C1ro f\t\nZv",
        substring="",
    )
    assert var_1 == 238
    testpilot_target_.how_many_times(string="I(McZ,@\r^skV", substring="LTP:LTP")
    var_9 = lambda *args, **kwargs: False
    var_10 = "[xb?(NnLMLnV5xU"
    testpilot_target_.how_many_times(string=var_9, substring=var_10)
