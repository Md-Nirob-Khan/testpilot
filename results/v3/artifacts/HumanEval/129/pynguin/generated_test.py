#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.minPath(grid=["gp7o:XCx2##6\r"], k=False)


def test_1():
    testpilot_target_.minPath(grid="`", k=True)


def test_2():
    testpilot_target_.minPath(grid=set(), k=1495)
