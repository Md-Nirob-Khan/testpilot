#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_51 = testpilot_target_.match_parens(
        lst="((\n    You are given a list of two strings, both strings consist of open\n    parentheses '(' or close parentheses ')' only.\n    Your job is to check if it is possible to concatenate the two strings in\n    some order, that the resulting string will be good.\n    A string S is considered to be good if and only if all parentheses in S\n    are balanced. For example: the string '(())()' is good, while the string\n    '())' is not.\n    Return 'Yes' if there's a way to make a good string, and return 'No' otherwise.\n\n    Examples:\n    match_parens(['()(', ')']) == 'Yes'\n    match_parens([')', ')']) == 'No'\n    (("
    )
    assert var_51 == "No"
