import pytest
from testpilot_target import check_if_last_char_is_a_letter

def test_check_if_last_char_is_a_letter():
    assert check_if_last_char_is_a_letter("apple pie") == False
    assert check_if_last_char_is_a_letter("apple pi e") == True
    assert check_if_last_char_is_a_letter("apple pi e ") == False
    assert check_if_last_char_is_a_letter("") == False