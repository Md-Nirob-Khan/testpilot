#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.encrypt(s=[])
    assert var_0 == ""
    testpilot_target_.encrypt(s=var_0)


@pytest.mark.xfail(strict=True)
def test_1():
    var_46 = testpilot_target_.encrypt(s=("(Dm!4b7t:s2&Z0G", "F72i.", "9L{[O.cHCFh"))
    assert var_46 == "(Dm!4b7t:s2&Z0GF72i.9L{[O.cHCFh"
    testpilot_target_.encrypt(s=26)


@pytest.mark.xfail(strict=True)
def test_2():
    var_3 = testpilot_target_.encrypt(
        s={
            "Create a function encrypt that takes a string as an argument and\n    returns a string encrypted with the alphabet being rotated. \n    The alphabet should be rotated in a manner such that the letters \n    shift down by two multiplied to two places.\n    For example:\n    encrypt('hi') returns 'lm'\n    encrypt('asdfghjkl') returns 'ewhjklnop'\n    encrypt('gf') returns 'kj'\n    encrypt('et') returns 'ix'\n    ": -1626.11,
            "abcdefghijklmnopqrstuvwxyz": False,
            "": True,
        }
    )
    assert (
        var_3
        == "Create a function encrypt that takes a string as an argument and\n    returns a string encrypted with the alphabet being rotated. \n    The alphabet should be rotated in a manner such that the letters \n    shift down by two multiplied to two places.\n    For example:\n    encrypt('hi') returns 'lm'\n    encrypt('asdfghjkl') returns 'ewhjklnop'\n    encrypt('gf') returns 'kj'\n    encrypt('et') returns 'ix'\n    ee"
    )
    var_46 = testpilot_target_.encrypt(s=var_3)
    assert (
        var_46
        == "Cviexi e jyrgxmsr irgvctx xlex xeoiw e wxvmrk ew er evkyqirx erh\n    vixyvrw e wxvmrk irgvctxih amxl xli eptlefix fimrk vsxexih. \n    Tli eptlefix wlsyph fi vsxexih mr e qerriv wygl xlex xli pixxivw \n    wlmjx hsar fc xas qypxmtpmih xs xas tpegiw.\n    Fsv ibeqtpi:\n    irgvctx('lm') vixyvrw 'pq'\n    irgvctx('ewhjklnop') vixyvrw 'ialnoprst'\n    irgvctx('kj') vixyvrw 'on'\n    irgvctx('ix') vixyvrw 'mb'\n    ii"
    )
    testpilot_target_.encrypt(s=26)
