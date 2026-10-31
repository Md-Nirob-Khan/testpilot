#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.eat(
        number=[False, 1658.08, "VhhQ:`\t$C"], need="|B^I]g{@m#(_>F{e\rJ*", remaining=""
    )


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.eat(number={}, need=False, remaining=True)
