from src.mathx import add, mul


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-2, 3) == 1


def test_mul_positive():
    assert mul(4, 5) == 20


def test_mul_negative():
    assert mul(-2, 3) == -6
