import pytest

from testpilot_target import words_string

def test_words_string():
    assert words_string("Hi, my name is John") == ["Hi", "my", "name", "is", "John"]
    assert words_string("One, two, three, four, five, six") == ["One", "two", "three", "four", "five", "six"]
    assert words_string("") == []
    assert words_string("No, commas or spaces") == ["No", "commas", "or", "spaces"]
    assert words_string("Single word") == ["Single", "word"]