import pytest

def digits(n):
    """Given a positive integer n, return the product of the odd digits.
    Return 0 if all digits are even.
    For example:
    digits(1)  == 1
    digits(4)  == 0
    digits(235) == 15
    """
    product = 1
    odd_count = 0
    for digit in str(n):
        int_digit = int(digit)
        if int_digit%2 == 1:
            product= product*int_digit
            odd_count+=1
    if odd_count ==0:
        return 0
    else:
        return product

def test_digits():
    assert digits(1) == 1
    assert digits(4) == 0
    assert digits(235) == 15
    assert digits(2468) == 0
    assert digits(13579) == 945
    assert digits(0) == 0
    assert digits(111) == 111
    assert digits(222) == 0
    assert digits(333) == 27
    assert digits(444) == 0
    assert digits(555) == 15
    assert digits(666) == 0
    assert digits(777) == 243
    assert digits(888) == 0
    assert digits(999) == 729