import pytest
from testpilot_target import sum_product

def test_sum_product_empty_list():
    assert sum_product([]) == (0, 1)

def test_sum_product_single_element_list():
    assert sum_product([1]) == (1, 1)

def test_sum_product_multiple_elements_list():
    assert sum_product([1, 2, 3, 4]) == (10, 24)

def test_sum_product_negative_numbers():
    assert sum_product([-1, -2, -3, -4]) == (-10, -24)

def test_sum_product_zero():
    assert sum_product([0]) == (0, 0)