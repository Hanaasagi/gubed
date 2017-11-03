# gubed

![](https://img.shields.io/badge/Python-27-A2D7DD.svg)
![](https://img.shields.io/badge/Python-34-7EC7D8.svg)

### What is gubed

gubed is the reversed string of debug. It is designed for quick debug in small application. I approval that PDB is better in some secse.

### Install

```Bash
git clone https://github.com/Hanaasagi/gubed.git
cd gubed
python setup.py install

# or just using pip
pip install git+https://github.com/Hanaasagi/gubed
```

### Utility Functions

#### 1) trace a function call


```Python
from gubed import trace


@trace
def func1(a, b):
    return a + b


def decorator(func):

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@trace
@decorator
def func2(a, b):
    return a * b


if __name__ == '__main__':
    func1(2, 3)
    # func1(2, 3) was called by <module> in trace_example.py line 17  return 5
    func2(2, 3)
    # func2(2, 3) was called by <module> in trace_example.py line 26  return 6
```

Maybe you can try `@trace(all_stack=True)` to show all call stack

#### 2) count

```Python

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
```

#### 3) REPL

```Python
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
```

#### 4) support autoload mode

when update code source file, the script will auto reload

```Python
from gubed import autoload

autoload()

# your code here

autoload()
```

### TODO

- [x] 自动检测代码改动，重新运行
- [ ] 查看变量的类型与值
- [x] 查看方法的调用者
- [ ] 自定义提示颜色
