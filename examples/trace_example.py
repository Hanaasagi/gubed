from gubed import trace


@trace
def func1(a, b):
    return a + b


def decorator(func):

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@trace(all_stack=True)
@decorator
def func2(a, b):
    return a * b


def func3(a, b):
    return func2(a, b)


if __name__ == '__main__':
    func1(2, 3)
    # func1(2, 3) was called by <module> in trace_example.py line 17  return 5
    func2(2, 3)
    # func2(2, 3) was called by <module> in trace_example.py line 26  return 6
    func3(2, 3)
