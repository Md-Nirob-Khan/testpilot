import pytest
from testpilot_target import iscube

def test_iscube():
    assert iscube(1) == True
    assert iscube(2) == False
    assert iscube(-1) == True
    assert iscube(64) == True
    assert iscube(0) == True
    assert iscube(180) == False