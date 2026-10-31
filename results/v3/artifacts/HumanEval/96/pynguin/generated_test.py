#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.count_up_to(n=1)


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.count_up_to(n=-230.28)
