#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.odd_count(lst=[])


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.odd_count(lst={-6732, -2709.03, False})
