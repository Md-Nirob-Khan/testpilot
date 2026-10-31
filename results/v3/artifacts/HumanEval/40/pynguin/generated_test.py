#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = testpilot_target_.triples_sum_to_zero(l=[])
    assert var_0 is False
    testpilot_target_.triples_sum_to_zero(l=var_0)


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.triples_sum_to_zero(
        l=b"\x16\x97l\x08\x07\x177;\x81\x9a\x06\x8f2\xb7\xa6\xb3\x8bk"
    )
    assert var_0 is False
    testpilot_target_.triples_sum_to_zero(l=None)


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.triples_sum_to_zero(l=[283, True])
    assert var_0 is False
    var_8 = testpilot_target_.triples_sum_to_zero(l=[var_0, var_0, False])
    assert var_8 is True
    testpilot_target_.triples_sum_to_zero(l=var_8)
