#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    var_0 = lambda *args, **kwargs: True
    testpilot_target_.sort_array(arr=var_0)
