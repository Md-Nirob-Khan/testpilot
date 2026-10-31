#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = "\x0b( &4[H\x0b<g/Mjkn_"
    testpilot_target_.correct_bracketing(brackets=var_0)
    var_2 = "\n\tVt'uDYo"
    var_3 = testpilot_target_.correct_bracketing(brackets=var_2)
    assert var_3 is False
    var_4 = testpilot_target_.correct_bracketing(brackets=())
    assert var_4 is True
    var_5 = ' brackets is a string of "<" and ">".\n    return True if every opening bracket has a corresponding closing bracket.\n\n    >>> correct_bracketing("<")\n    False\n    >>> correct_bracketing("<>")\n    True\n    >>> correct_bracketing("<<><>>")\n    True\n    >>> correct_bracketing("><<>")\n    False\n    '
    testpilot_target_.correct_bracketing(brackets=var_5)
    var_7 = "6O#LuNaLs3Ec|"
    testpilot_target_.correct_bracketing(brackets=var_7)
    testpilot_target_.correct_bracketing(brackets=())


def test_1():
    var_0 = "41C+:dGAW"
    var_1 = testpilot_target_.correct_bracketing(brackets=var_0)
    assert var_1 is False
    testpilot_target_.correct_bracketing(brackets=var_0)


@pytest.mark.xfail(strict=True)
def test_2():
    testpilot_target_.correct_bracketing(
        brackets=' brackets is a string of "<" and ">".\n    return True if every opening bracket has a corresponding closing bracket.\n\n    >>> correct_bracketing("<")\n    False\n    >>> correct_bracketing("<>")\n    True\n    >>> correct_bracketing("<<><>>")\n    True\n    >>> correct_bracketing("><<>")\n    False\n    < brackets is a string of "<" and ">".\n    return True if every opening bracket has a corresponding closing bracket.\n\n    >>> correct_bracketing("<")\n    False\n    >>> correct_bracketing("<>")\n    True\n    >>> correct_bracketing("<<><>>")\n    True\n    >>> correct_bracketing("><<>")\n    False\n    < brackets is a string of "<" and ">".\n    return True if every opening bracket has a corresponding closing bracket.\n\n    >>> correct_bracketing("<")\n    False\n    >>> correct_bracketing("<>")\n    True\n    >>> correct_bracketing("<<><>>")\n    True\n    >>> correct_bracketing("><<>")\n    False\n    < brackets is a string of "<" and ">".\n    return True if every opening bracket has a corresponding closing bracket.\n\n    >>> correct_bracketing("<")\n    False\n    >>> correct_bracketing("<>")\n    True\n    >>> correct_bracketing("<<><>>")\n    True\n    >>> correct_bracketing("><<>")\n    False\n    '
    )
    var_1 = "b"
    var_2 = testpilot_target_.correct_bracketing(brackets=var_1)
    assert var_2 is False
    var_3 = testpilot_target_.correct_bracketing(brackets={0, 639})
    assert var_3 is False
    var_4 = "<\tjukmQ3m GQ\\"
    testpilot_target_.correct_bracketing(brackets=var_4)
    var_6 = testpilot_target_.correct_bracketing
    testpilot_target_.correct_bracketing(brackets=var_6)
