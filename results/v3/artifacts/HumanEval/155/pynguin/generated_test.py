#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.even_odd_count(num=complex(-1344.162032, -1598.58022))


def test_1():
    testpilot_target_.even_odd_count


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.even_odd_count(num=complex(1641.394406, -3054.3425593))


def test_3():
    testpilot_target_.even_odd_count(num=0)
