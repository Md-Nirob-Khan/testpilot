#  This file was automatically generated using Pynguin.

import pytest
import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


@pytest.mark.xfail(strict=True)
def test_0():
    testpilot_target_.Strongest_Extension(
        class_name={
            ".": 0,
            "You will be given the name of a class (a string) and a list of extensions.\n    The extensions are to be used to load additional classes to the class. The\n    strength of the extension is as follows: Let CAP be the number of the uppercase\n    letters in the extension's name, and let SM be the number of lowercase letters \n    in the extension's name, the strength is given by the fraction CAP - SM. \n    You should find the strongest extension and return a string in this \n    format: ClassName.StrongestExtensionName.\n    If there are two or more extensions with the same strength, you should\n    choose the one that comes first in the list.\n    For example, if you are given \"Slices\" as the class and a list of the\n    extensions: ['SErviNGSliCes', 'Cheese', 'StuFfed'] then you should\n    return 'Slices.SErviNGSliCes' since 'SErviNGSliCes' is the strongest extension \n    (its strength is -1).\n    Example:\n    for Strongest_Extension('my_class', ['AA', 'Be', 'CC']) == 'my_class.AA'\n    ": -247,
            "You will be given the name of a class (a string) and a list of extensions.\n    The extensions are to be used to load additional classes to the class. The\n    strength of the extension is as follows: Let CAP be the number of the uppercase\n    letters in the extension's name, and let SM be the number of lowercase letters \n    in the extension's name, the strength is given by the fraction CAP - SM. \n    You should find the strongest extension and return a string in this \n    format: ClassName.StrongestExtensionName.\n    If there are two or more extensions with the same strength, you should\n    choose the one that comes first in the list.\n    For example, if you are given \"Slices\" as the class and a list of the\n    extensions: ['SErviNGSliCes', 'Cheese', 'StuFfed'] then you should\n    return 'Slices.SErviNGSliCes' since 'SErviNGSliCes' is the strongest extension \n    (its strength is -1).\n    Example:\n    for Strongest_Extension('my_class', ['AA', 'Be', 'CC']) == 'my_class.AA'\n    ": -74.57,
        },
        extensions="B",
    )


@pytest.mark.xfail(strict=True)
def test_1():
    testpilot_target_.Strongest_Extension(
        class_name=complex(2618.0, 1791.747), extensions='"Q\r)fL'
    )
