import pytest
from testpilot_target import int_to_mini_roman

@pytest.mark.parametrize("number, expected", [
    (19, 'xix'),
    (152, 'clii'),
    (426, 'cdxxvi'),
])
def test_int_to_mini_roman(number, expected):
    assert int_to_mini_roman(number) == expected