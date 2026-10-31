#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.filter_by_substring(
        strings=b"bv\x94\x8d\xf4\xca\xbd\xe5\ns\xe8\xcf\x92\xa60R\x9a", substring=True
    )
