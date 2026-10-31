#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.select_words(s="RJBBl4_/\tC", n=False)


def test_1():
    testpilot_target_.select_words(
        s='Given a string s and a natural number n, you have been tasked to implement \n    a function that returns a list of all words from string s that contain exactly \n    n consonants, in order these words appear in the string s.\n    If the string s is empty then the function should return an empty list.\n    Note: you may assume the input string contains only letters and spaces.\n    Examples:\n    select_words("Mary had a little lamb", 4) ==> ["little"]\n    select_words("Mary had a little lamb", 3) ==> ["Mary", "lamb"]\n    select_words("simple white space", 2) ==> []\n    select_words("Hello world", 4) ==> ["world"]\n    select_words("Uncle sam", 3) ==> ["Uncle"]\n    uouo',
        n=3704.83,
    )


def test_2():
    testpilot_target_.select_words(s="'fI1\x0c='#J66l/<<6", n=3)
