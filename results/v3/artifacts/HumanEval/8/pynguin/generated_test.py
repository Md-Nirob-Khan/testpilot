#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.sum_product(numbers=[])
    var_1 = var_0[0]
    assert var_1 == 0
    var_2 = var_0[1]
    assert var_2 == 1
    testpilot_target_.sum_product(numbers=var_2)


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.sum_product(numbers=(-2321.96,))
    var_1 = var_0[0]
    assert var_1 == pytest.approx(-2321.96, abs=0.01, rel=0.01)
    var_2 = var_0[1]
    assert var_2 == pytest.approx(-2321.96, abs=0.01, rel=0.01)
    testpilot_target_.sum_product(numbers=("H\\]P}lXg<'3O", 1))


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.sum_product(numbers=None)
