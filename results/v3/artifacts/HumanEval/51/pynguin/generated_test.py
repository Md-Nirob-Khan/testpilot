#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.remove_vowels(text="hX\\&*/E\nU;}#S)")
    var_1 = testpilot_target_.remove_vowels(text="9|AuyGE(ahjtN_")
    assert var_1 == "9|yG(hjtN_"
