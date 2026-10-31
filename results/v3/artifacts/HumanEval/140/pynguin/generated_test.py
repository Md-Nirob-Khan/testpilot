#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_26 = testpilot_target_.fix_spaces(text=())
    assert var_26 == ""


def test_1():
    var_0 = testpilot_target_.fix_spaces(text='%l^MlhyCy"i8lTzRCZ')
    assert var_0 == '%l^MlhyCy"i8lTzRCZ'


def test_2():
    var_0 = testpilot_target_.fix_spaces(text="hQeEf3U1 I\\")
    assert var_0 == "hQeEf3U1_I\\"


def test_3():
    var_0 = testpilot_target_.fix_spaces(
        text='\n    Given a string text, replace all spaces in it with underscores, \n    and if a string has more than 2 consecutive spaces, \n    then replace all consecutive spaces with - \n    \n    fix_spaces("Example") == "Example"\n    fix_spaces("Example 1") == "Example_1"\n    fix_spaces(" Example 2") == "_Example_2"\n    fix_spaces(" Example   3") == "_Example-3"\n    .\n    Given a string text, replace all spaces in it with underscores, \n    and if a string has more than 2 consecutive spaces, \n    then replace all consecutive spaces with - \n    \n    fix_spaces("Example") == "Example"\n    fix_spaces("Example 1") == "Example_1"\n    fix_spaces(" Example 2") == "_Example_2"\n    fix_spaces(" Example   3") == "_Example-3"\n    '
    )
    assert (
        var_0
        == '\n-Given_a_string_text,_replace_all_spaces_in_it_with_underscores,_\n-and_if_a_string_has_more_than_2_consecutive_spaces,_\n-then_replace_all_consecutive_spaces_with_-_\n-\n-fix_spaces("Example")_==_"Example"\n-fix_spaces("Example_1")_==_"Example_1"\n-fix_spaces("_Example_2")_==_"_Example_2"\n-fix_spaces("_Example-3")_==_"_Example-3"\n-.\n-Given_a_string_text,_replace_all_spaces_in_it_with_underscores,_\n-and_if_a_string_has_more_than_2_consecutive_spaces,_\n-then_replace_all_consecutive_spaces_with_-_\n-\n-fix_spaces("Example")_==_"Example"\n-fix_spaces("Example_1")_==_"Example_1"\n-fix_spaces("_Example_2")_==_"_Example_2"\n-fix_spaces("_Example-3")_==_"_Example-3"\n-'
    )


def test_4():
    var_26 = testpilot_target_.fix_spaces(text=[])
    assert var_26 == ""
    var_28 = testpilot_target_.fix_spaces(text="9 ")
    assert var_28 == "9_"
