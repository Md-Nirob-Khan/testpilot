#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.histogram(test="")


def test_1():
    testpilot_target_.histogram(
        test="    Given a string representing a space separated lowercase letters, return a dictionary\n    of the letter with the most repetition and containing the corresponding count.\n    If several letters have the same occurrence, return all of them.\n    \n    Example:\n    histogram('a b c') == {'a': 1, 'b': 1, 'c': 1}\n    histogram('a b b a') == {'a': 2, 'b': 2}\n    histogram('a b c a b') == {'a': 2, 'b': 2}\n    histogram('b b b b a') == {'b': 4}\n    histogram('') == {}\n\n      "
    )


def test_2():
    lambda *args, **kwargs: []
