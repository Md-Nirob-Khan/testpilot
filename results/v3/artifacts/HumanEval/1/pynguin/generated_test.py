#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_8 = 'r"yFAH),g+!H^'
    testpilot_target_.separate_paren_groups(paren_string=var_8)


def test_1():
    var_12 = "JM Input to this function is a string containing multiple groups of nested parentheses. Your goal is to\n    separate those group into separate strings and return the list of those.\n    Separate groups are balanced (each open brace is properly closed) and not nested within each other\n    Ignore any spaces in the input string.\n    >>> separate_paren_groups('( ) (( )) (( )( ))')\n    ['()', '(())', '(()())']\n    "
    testpilot_target_.separate_paren_groups(paren_string=var_12)
