#  This file was automatically generated using Pynguin.

import sys
import testpilot_target

testpilot_target_ = sys.modules["testpilot_target"]


def test_0():
    testpilot_target_.sorted_list_sum(
        lst=[
            'Write a function that accepts a list of strings as a parameter,\n    deletes the strings that have odd lengths from it,\n    and returns the resulted list with a sorted order,\n    The list is always a list of strings and never an array of numbers,\n    and it may contain duplicates.\n    The order of the list should be ascending by length of each word, and you\n    should return the list sorted by that rule.\n    If two words have the same length, sort the list alphabetically.\n    The function should return a list of strings in sorted order.\n    You may assume that all words will have the same length.\n    For example:\n    assert list_sort(["aa", "a", "aaa"]) => ["aa"]\n    assert list_sort(["ab", "a", "aaa", "cd"]) => ["ab", "cd"]\n    '
        ]
    )


def test_1():
    testpilot_target_.sorted_list_sum(lst=["L+Q"])
