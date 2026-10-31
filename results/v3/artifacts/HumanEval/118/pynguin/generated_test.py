#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    var_12 = testpilot_target_.get_closest_vowel(word="z6oej^")
    assert var_12 == ""


def test_1():
    var_3 = testpilot_target_.get_closest_vowel(word=[])
    assert var_3 == ""


@pytest.mark.xfail(strict=True)
def test_2():
    var_9 = testpilot_target_.get_closest_vowel(
        word=b"\xaaX\xb5\x10\x8c\x8aJ\xe4L\xd9("
    )
    assert var_9 == ""
    var_24 = testpilot_target_.get_closest_vowel(word='2bO#Wur-J66A"/@')
    assert var_24 == "A"
    testpilot_target_.get_closest_vowel(word=2)
