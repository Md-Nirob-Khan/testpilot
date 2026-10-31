#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.count_upper(
        s="AEIOU.\n    Given a string s, count the number of uppercase vowels in even indices.\n    \n    For example:\n    count_upper('aBCdEf') returns 1\n    count_upper('abcdefg') returns 0\n    count_upper('dBBE') returns 0\n    "
    )
    assert var_0 == 5
    testpilot_target_.count_upper(s=var_0)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.count_upper(s=(3551.42, True))


def test_2():
    testpilot_target_.count_upper
