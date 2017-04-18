# -*-coding:UTF-8-*-
import os
import sys
import time
import tempfile
import threading
import subprocess
import functools
import signal


py3 = sys.version_info >= (3,)
if py3:
    import _thread as thread
else:
    import thread


_terminal_color = '\x1b[37m\x1b[46m\x1b[1m{message}\x1b[0m'  # pants color


def _log(message):
    """debug log
    """
    print(_terminal_color.format(message=message))


def debug(func):
    @functools.wrapper(func)
    def wrapper(*args, **kwargs):
        pass
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
                # A None value indicates that the process hasn’t terminated yet.
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

    if os.environ.get('GUBED_APP', False):
        def signal_handler(signal, frame):
            if not bgcheck.status:
                bgcheck.status = 'exit'
            bgcheck.join()
            if bgcheck.status == 'reload':
                # subprocess exit and send signal 3
                sys.exit(3)
        lockfile = os.environ.get('GUBED_LOCKFILE')
        bgcheck = FileCheckerThread(lockfile, interval)
        # signal.SIGINT is KeyboardInterrupt singal
        signal.signal(signal.SIGINT, signal_handler)
        bgcheck.start()


class FileCheckerThread(threading.Thread):

    def __init__(self, lockfile, interval):
        super(FileCheckerThread, self).__init__()
        self.lockfile, self.interval = lockfile, interval
        self.status = None

    def run(self):
        mtime = lambda path: os.stat(path).st_mtime
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
            if not os.path.exists(self.lockfile)\
            or mtime(self.lockfile) < time.time() - self.interval - 5:
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
