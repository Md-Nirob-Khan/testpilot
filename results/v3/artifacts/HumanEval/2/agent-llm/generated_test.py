import pytest
from testpilot_target import truncate_number

def test_truncate_number():
    assert truncate_number(1.1) == 0.1