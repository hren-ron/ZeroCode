
from examples.buggy_calculator import add, subtract


def test_add():
    assert add(3, 2) == 5


def test_subtract():
    assert subtract(10, 3) == 7


def test_subtract_negative_result():
    assert subtract(3, 10) == -7
