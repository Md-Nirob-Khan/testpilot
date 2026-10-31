#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.unique_digits(
        x=b"\x16\x97l\x08\x07\x177;\x81\x9a\x06\x8f2\xb7\xa6\xb3\x8bk"
    )


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.unique_digits(x="Y2LG]eR-D")


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.unique_digits(x=-230.28)
