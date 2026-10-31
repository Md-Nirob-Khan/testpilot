#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.numerical_letter_grade(grades=(3.3,))


def test_1():
    testpilot_target_.numerical_letter_grade(grades=b"q\x028\xbe\x05\xc2G")


def test_2():
    testpilot_target_.numerical_letter_grade(grades=(-3700, 0, True))


def test_3():
    testpilot_target_.numerical_letter_grade(
        grades=b"\x97b<\x93\x05H\x04\xa4\xc8\xdb\x93"
    )


def test_4():
    testpilot_target_.numerical_letter_grade(
        grades=b"\xb8\xb4\xc3\xbbj\x05\x03\xbe\xd4\x8a\x9a\xeb&\x18\xbc\x96\xca"
    )


def test_5():
    testpilot_target_.numerical_letter_grade(grades=(0.7, True))


def test_6():
    testpilot_target_.numerical_letter_grade(grades=[2.7, False])
    testpilot_target_.numerical_letter_grade(grades={-3700, 1.7})


@pytest.mark.xfail(strict=True)
def test_7():
    testpilot_target_.numerical_letter_grade(grades=(2.3, "x0v3U/?.fJz"))


@pytest.mark.xfail(strict=True)
def test_8():
    testpilot_target_.numerical_letter_grade(grades=(False, 3.7, "mPgLHBW"))


def test_9():
    testpilot_target_.numerical_letter_grade(grades=(848.79, True, 849))
    testpilot_target_.numerical_letter_grade(grades=[1.3, -842, 2223.76])
