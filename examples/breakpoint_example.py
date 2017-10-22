from gubed import breakpoint


def func(*args, **kwargs):
    breakpoint(args=args, kwargs=kwargs)


if __name__ == '__main__':
    func(1, 2, 3, 4, 5, x=101)
    # you will enter REPL
    # In [1]: args
    # Out[1]: (1, 2, 3, 4, 5)

    # In [2]: kwargs
    # Out[2]: {'x': 101}
