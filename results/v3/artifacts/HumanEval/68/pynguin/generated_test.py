#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.pluck(arr="yV$iT")


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.pluck(arr=-230.28)


def test_2():
    testpilot_target_.pluck(arr=b"\xe6\x8b\x90\xa8\x08-\xed\xd9P")


def test_3():
    testpilot_target_.pluck(arr=set())


def test_4():
    var_3 = (-2111, 821.98)
    testpilot_target_.pluck(arr=var_3)
