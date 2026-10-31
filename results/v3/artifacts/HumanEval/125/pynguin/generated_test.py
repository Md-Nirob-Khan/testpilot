#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_4 = testpilot_target_.split_words(txt=())
    assert var_4 == 0


@pytest.mark.xfail(strict=True)
def test_1():
    var_0 = testpilot_target_.split_words(txt="[Ma\x0b<Bv|9ayjM|>j N")
    var_1 = testpilot_target_.split_words(txt=var_0)
    assert var_1 == 0
    testpilot_target_.split_words(txt=str)


@pytest.mark.xfail(strict=True)
def test_2():
    var_55 = testpilot_target_.split_words(txt="\x0c")
    assert var_55 == 0
    testpilot_target_.split_words(
        txt={
            ",": 2551.27,
            ",": '\n    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you\n    should split on commas \',\' if no commas exists you should return the number of lower-case letters with odd order in the\n    alphabet, ord(\'a\') = 0, ord(\'b\') = 1, ... ord(\'z\') = 25\n    Examples\n    split_words("Hello world!") ➞ ["Hello", "world!"]\n    split_words("Hello,world!") ➞ ["Hello", "world!"]\n    split_words("abcdef") == 3 \n     , \n    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you\n    should split on commas \',\' if no commas exists you should return the number of lower-case letters with odd order in the\n    alphabet, ord(\'a\') = 0, ord(\'b\') = 1, ... ord(\'z\') = 25\n    Examples\n    split_words("Hello world!") ➞ ["Hello", "world!"]\n    split_words("Hello,world!") ➞ ["Hello", "world!"]\n    split_words("abcdef") == 3 \n     \n    Given a string of words, return a list of words split on whitespace, if no whitespaces exists in the text you\n    should split on commas \',\' if no commas exists you should return the number of lower-case letters with odd order in the\n    alphabet, ord(\'a\') = 0, ord(\'b\') = 1, ... ord(\'z\') = 25\n    Examples\n    split_words("Hello world!") ➞ ["Hello", "world!"]\n    split_words("Hello,world!") ➞ ["Hello", "world!"]\n    split_words("abcdef") == 3 \n    ',
        }
    )
