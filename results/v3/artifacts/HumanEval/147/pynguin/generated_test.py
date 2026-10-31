#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_14 = testpilot_target_.get_max_triples(n=True)
    assert var_14 == 0
    var_18 = lambda *args, **kwargs: [-416, "[P\r)4WbEw"]
    testpilot_target_.get_max_triples(n=var_18)


@pytest.mark.xfail(strict=True)
def test_1():
    var_14 = testpilot_target_.get_max_triples(n=43)
    assert var_14 == 4018
    testpilot_target_.get_max_triples(n=complex(-921.0, -85.7))
