# -*-coding:UTF-8-*-

import os
import sys
import time
import tempfile
import threading
import subprocess
import functools
import inspect
import traceback
import signal


PY3 = sys.version_info >= (3,)

if PY3:
    import _thread as thread
else:
    import thread


_terminal_color = '\x1b[37m\x1b[46m\x1b[1m{message}\x1b[0m'  # pants color

_stressed_color = '\x1b[37m\x1b[33m\x1b[1m{message}\x1b[0m'


def _log(message, color=_terminal_color):
    """colorful terminal debug log
    """
    print(color.format(message=message))


def trace(all_stack):
    if callable(all_stack):
        return _trace(all_stack)

    if not isinstance(all_stack, bool):
        raise TypeError('must be boolean')

    return functools.partial(_trace, all_stack=all_stack)


def _trace(func, all_stack=False):
    """trace the function call
    notice that this should be the outermost decorator
    ```
    @trace
    @other
    def func():
        pass
    ```
    """

    # handle closure
    while func.__closure__ is not None:
        func = func.__closure__[0].cell_contents

    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 4 elements tuple (filename, line number, function name, text)
        caller = traceback.extract_stack()[-2]
        result = func(*args, **kwargs)
        fmt = ('{0.line} [sig: {1}] was called by {0.name} in '
               '{0.filename} line {0.lineno}  return {2}')
        _log(fmt.format(caller, tuple(sig.parameters.keys()), result))
        if all_stack:
            _log('stack message:', _stressed_color)
            stack_msgs = inspect.stack()
            for stack_msg in stack_msgs[1:]:
                _log('{} line {}'.format(stack_msg.filename, stack_msg.lineno))
        return result
    return wrapper


def breakpoint(**inject_var):
    """send vairable to REPL"""
    info = inspect.getframeinfo(sys._getframe(1), context=5)
    filename = info.filename
    lineno = info.lineno
    context = ''.join(info.code_context)
    banner = '[line {} in {}]\n{}'.format(lineno,
                                          filename, context).strip()
    try:
        from IPython import embed
        embed(banner1=banner, user_ns=inject_var)
    except ImportError:
        from code import interact
        interact(banner=banner, local=inject_var)


def timeit(func):
    """Time execution of function
    warning: it may be interfered by other process
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        time_init = time.time()
        result = func(*args, **kwargs)
        _log('cost {}'.format(time.time() - time_init))
        return result
    return wrapper


def countit(func):
    """count the number of function executions
    warning: it may be interfered by other process
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper._counter += 1
        result = func(*args, **kwargs)
        return result

    wrapper._counter = 0

    return wrapper


def autoload(interval=1):
    """autoload the user code, work as the following control flow

    -----------         -----------
    |         |  poll() |         |
    |  main   |   ==>   |   sub   | exec user code
    | process |   <==   | process |
    |         |  signal |         |
    -----------         -----------
                         ||    /\
                         \/    || if file updated, `thread.interrupt_main()`
                        -----------
                        |         |
                        |  check  |
                        |  file   |
                        |  thread |
                        -----------
    """
    # os.environ['GUBED_APP'] is vairable to identify main/sub process
    if not os.environ.get('GUBED_APP'):
        _log('autoload mode start')
        try:
            lockfile = None
            fd, lockfile = tempfile.mkstemp(prefix='GUBED_APP', suffix='.lock')
            os.close(fd)

            while os.path.exists(lockfile):
                args = [sys.executable] + sys.argv
                environ = os.environ.copy()
                environ['GUBED_APP'] = 'true'
                environ['GUBED_LOCKFILE'] = lockfile

                # execute the code in the same environment
                p = subprocess.Popen(args, env=environ)

                # Check if child process has terminated
                # A None value indicates that the process hasn’t terminated yet
                while p.poll() is None:
                    # update the modified time
                    os.utime(lockfile, None)
                    time.sleep(interval)

                if p.poll() != 3:
                    if os.path.exists(lockfile):
                        os.unlink(lockfile)
                    sys.exit(p.poll())
        except KeyboardInterrupt:
            _log('\nUser Exit[<Ctrl-C>]')
        finally:
            if os.path.exists(lockfile):
                os.unlink(lockfile)
        # no return because it is a function
        sys.exit()

    elif os.environ.get('GUBED_APP_CHECK'):
        while True:
            time.sleep(2)

    elif os.environ.get('GUBED_APP', False):
        def interrupt_handler(signal, frame):
            if not bgcheck.status:
                bgcheck.status = 'exit'
            bgcheck.join()
            if bgcheck.status == 'reload':
                # subprocess exit and send signal 3
                sys.exit(3)
            sys.exit()
        lockfile = os.environ.get('GUBED_LOCKFILE')
        bgcheck = FileCheckerThread(lockfile, interval)
        # signal.SIGINT is KeyboardInterrupt singal
        signal.signal(signal.SIGINT, interrupt_handler)
        bgcheck.start()
        os.environ['GUBED_APP_CHECK'] = 'true'
        return

    else:
        # never execute
        raise Exception('unexcept bug')


class FileCheckerThread(threading.Thread):

    def __init__(self, lockfile, interval):
        super(FileCheckerThread, self).__init__()
        self.lockfile, self.interval = lockfile, interval
        self.status = None

    def run(self):
        mtime = lambda path: os.stat(path).st_mtime  # noqa
        files = dict()

        # get all imported modules and their filepath
        for module in list(sys.modules.values()):
            path = getattr(module, '__file__', '')
            # if file extension are pyo or pyc, change to py
            if path[-4:] in ('.pyo', '.pyc'):
                path = path[:-1]
            if path and os.path.exists(path):
                files[path] = mtime(path)

        while not self.status:
            if not os.path.exists(self.lockfile) or \
                    mtime(self.lockfile) < time.time() - self.interval - 5:
                self.status = 'error'
                thread.interrupt_main()

            # check the all file modified time
            for path, lmtime in list(files.items()):
                if not os.path.exists(path) or mtime(path) > lmtime:
                    self.status = 'reload'
                    # raise a KeyboardInterrupt exception in the main thread.
                    thread.interrupt_main()
                    break
            time.sleep(self.interval)
