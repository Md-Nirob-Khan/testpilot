import pytest
from testpilot_target import check_dict_case

@pytest.mark.parametrize("dict, expected", [
    ({"a":"apple", "b":"banana"}, True),
    ({"a":"apple", "A":"banana", "B":"banana"}, False),
    ({"a":"apple", 8:"banana", "a":"apple"}, False),
    ({"Name":"John", "Age":"36", "City":"Houston"}, False),
    ({"STATE":"NC", "ZIP":"12345"}, True),
])
def test_check_dict_case(dict, expected):
    assert check_dict_case(dict) == expected