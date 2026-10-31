#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_36 = testpilot_target_.search(
        lst=b"\x18\x97VE\x11\x91\xcd\x87ym5X\xcb\x13\xa6\xd2M\x81\xcd"
    )
    assert var_36 == -1


@pytest.mark.xfail(strict=True)
def test_1():
    var_29 = testpilot_target_.search(lst=b"U\xd1#\x1f\xd93p\xf8j\xc4\xc4\x01")
    assert var_29 == 1
    testpilot_target_.search(lst=var_29)
