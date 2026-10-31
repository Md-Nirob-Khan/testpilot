#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.bf(planet1="EarthSaturn", planet2=bytes)
    testpilot_target_.bf(planet1="Jupiter", planet2=None)


def test_1():
    testpilot_target_.bf(planet1="Jupiter", planet2=None)


def test_2():
    var_53 = "Earth"
    testpilot_target_.bf(planet1=var_53, planet2=var_53)


def test_3():
    var_53 = "Earth"
    testpilot_target_.bf(planet1=var_53, planet2="Mars")


def test_4():
    var_53 = "Jupiter"
    testpilot_target_.bf(planet1=var_53, planet2="Mars")
