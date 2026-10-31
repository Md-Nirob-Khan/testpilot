#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.will_it_fly(q=(-1158.64, 622.08), w=4324.88)
    assert var_0 is False


@pytest.mark.xfail(strict=True)
def test_1():
    var_34 = testpilot_target_.will_it_fly(q=b"\x92\xba@", w=False)
    assert var_34 is False
    testpilot_target_.will_it_fly(q=937.0, w=["a&V&{K9+e7)#p,'jlF%", 5058.45])


@pytest.mark.xfail(strict=True)
def test_2():
    var_0 = testpilot_target_.will_it_fly(q="", w=2511.09)
    assert var_0 is True
    testpilot_target_.will_it_fly(q=(False, '.3{`J++i+o"'), w=var_0)


def test_3():
    var_0 = testpilot_target_.will_it_fly(q=(False, True, False), w=True)
    assert var_0 is True
