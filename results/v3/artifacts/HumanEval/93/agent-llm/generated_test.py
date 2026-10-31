import pytest
from testpilot_target import encode

def test_encode():
    assert encode('test') == 'TGST'
    assert encode('This is a message') == 'tHKS KS C MGSSCGG'
    assert encode('Python') == 'pYtHn'
    assert encode('123') == '123'
    assert encode('') == ''