def square(x):
    return x * x


def test_square_int():
    assert square(2) == 4
    assert square(5) == 25
    assert square(10) == 100


def test_square_float():
    assert square(1.5) == 2.25
