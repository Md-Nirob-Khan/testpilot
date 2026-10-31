#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_58 = testpilot_target_.intersection(
        interval1=(-1576.7, -2175),
        interval2=b'S\x9e\xb7J\xc7\xa3S\xfa\xc9\x95"\xb4\xf8\x10\x1d\xb6\x8fU\xbf',
    )
    assert var_58 == "NO"


def test_1():
    var_58 = testpilot_target_.intersection(
        interval1=b"\x96\xd5\xae\x9e!",
        interval2=b"\x03\xbeIR\xe2y\xe1D\xb6\x01\xa9\x8d\xe3R\x0c",
    )
    assert var_58 == "NO"


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.intersection(
        interval1=b"&\xc3\x1c4\xa4\xaa\x8d", interval2=(False, 3644.58)
    )
    assert var_0 == "YES"
    testpilot_target_.intersection(interval1=var_0, interval2=var_0)
