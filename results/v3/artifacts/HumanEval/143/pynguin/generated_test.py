#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_36 = testpilot_target_.words_in_sentence(
        sentence='\n    You are given a string representing a sentence,\n    the sentence contains some words separated by a space,\n    and you have to return a string that contains the words from the original sentence,\n    whose lengths are prime numbers,\n    the order of the words in the new string should be the same as the original one.\n\n    Example 1:\n        Input: sentence = "This is a test"\n        Output: "is"\n\n    Example 2:\n        Input: sentence = "lets go for swimming"\n        Output: "go for"\n\n    Constraints:\n        * 1 <= len(sentence) <= 100\n        * sentence contains only letters\n    '
    )
    assert (
        var_36
        == 'You are given the words by and you to the words the whose lengths are prime the order of the words in the new be the as the Example 1: "This is test" Output: Example 2: "lets go for Output: "go <= len(sentence) <= 100 letters'
    )
