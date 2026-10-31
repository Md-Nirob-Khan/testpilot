#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.vowels_count(s=set())


@pytest.mark.xfail(strict=True)
def test_1():
    var_2 = testpilot_target_.vowels_count(
        s="Write a function vowels_count which takes a string representing\n    a word as input and returns the number of vowels in the string.\n    Vowels in this case are 'a', 'e', 'i', 'o', 'u'. Here, 'y' is also a\n    vowel, but only when it is at the end of the given word.\n\n    Example:\n    >>> vowels_count(\"abcde\")\n    2\n    >>> vowels_count(\"ACEDY\")\n    3\n    "
    )
    assert var_2 == 85
    assert testpilot_target_.FIX == "\nAdd more test cases.\n"
    testpilot_target_.vowels_count(s=complex(-224.763991, 1146.3))


@pytest.mark.xfail(strict=True)
def test_2():
    var_14 = testpilot_target_.vowels_count(s="Y")
    assert var_14 == 1
    assert testpilot_target_.FIX == "\nAdd more test cases.\n"
    testpilot_target_.vowels_count(s=complex(287.955062, -342.0096692))


def test_3():
    var_14 = testpilot_target_.vowels_count(s="Y")
    assert var_14 == 1
    assert testpilot_target_.FIX == "\nAdd more test cases.\n"
    var_33 = testpilot_target_.vowels_count(
        s="aeiouAEIOUyaeiouAEIOUyWrite a function vowels_count which takes a string representing\n    a word as input and returns the number of vowels in the string.\n    Vowels in this case are 'a', 'e', 'i', 'o', 'u'. Here, 'y' is also a\n    vowel, but only when it is at the end of the given word.\n\n    Example:\n    >>> vowels_count(\"abcde\")\n    2\n    >>> vowels_count(\"ACEDY\")\n    3\n    yy"
    )
    assert var_33 == 106
