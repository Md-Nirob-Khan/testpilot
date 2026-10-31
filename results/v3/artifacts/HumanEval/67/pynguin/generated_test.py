#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.fruit_distribution(
        s='\n    In this task, you will be given a string that represents a number of apples and oranges \n    that are distributed in a basket of fruit this basket contains \n    apples, oranges, and mango fruits. Given the string that represents the total number of \n    the oranges and apples and an integer that represent the total number of the fruits \n    in the basket return the number of the mango fruits in the basket.\n    for examble:\n    fruit_distribution("5 apples and 6 oranges", 19) ->19 - 5 - 6 = 8\n    fruit_distribution("0 apples and 1 oranges",3) -> 3 - 0 - 1 = 2\n    fruit_distribution("2 apples and 3 oranges", 100) -> 100 - 2 - 3 = 95\n    fruit_distribution("100 apples and 1 oranges",120) -> 120 - 100 - 1 = 19\n     \n    In this task, you will be given a string that represents a number of apples and oranges \n    that are distributed in a basket of fruit this basket contains \n    apples, oranges, and mango fruits. Given the string that represents the total number of \n    the oranges and apples and an integer that represent the total number of the fruits \n    in the basket return the number of the mango fruits in the basket.\n    for examble:\n    fruit_distribution("5 apples and 6 oranges", 19) ->19 - 5 - 6 = 8\n    fruit_distribution("0 apples and 1 oranges",3) -> 3 - 0 - 1 = 2\n    fruit_distribution("2 apples and 3 oranges", 100) -> 100 - 2 - 3 = 95\n    fruit_distribution("100 apples and 1 oranges",120) -> 120 - 100 - 1 = 19\n      ',
        n=None,
    )


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.fruit_distribution(s=None, n=complex(-1449.498, -3877.03204))
