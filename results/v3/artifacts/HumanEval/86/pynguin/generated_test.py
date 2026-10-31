#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_0 = testpilot_target_.anti_shuffle(s="hX\\&*/E\nU;}#S)")
    assert var_0 == "\n#&)*/;ESUX\\h}"
    testpilot_target_.anti_shuffle(s="9|AuyGE(ahjtN_")
