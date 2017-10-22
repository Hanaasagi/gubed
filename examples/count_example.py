from gubed import timeit, countit


@timeit
def func1(a, b):
    return a + b


@countit
def func2(a, b):
    return a * b


@countit
def func3(a, b):
    return a ** b


if __name__ == '__main__':
    func1(2, 3)
    # cost 2.1457672119140625e-06

    for _ in range(10):
        func2(1, 1)

    assert func2._counter == 10
    assert func3._counter == 0
