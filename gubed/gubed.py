# -*-coding:UTF-8-*-

import os
import sys
import time
import tempfile
import threading
import thread
import subprocess
import signal

"""
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

def debug_mod(interval=1):
    if not os.environ.get('GUBED_APP'):
        try:
            lockfile = None
            fd, lockfile = tempfile.mkstemp(prefix='GUBED_APP', suffix='.lock')
            os.close(fd)

            while os.path.exists(lockfile):
                args = [sys.executable] + sys.argv
                environ = os.environ.copy()
                environ['GUBED_APP'] = 'true'
                environ['GUBED_LOCKFILE'] = lockfile

                p = subprocess.Popen(args, env=environ)

                while p.poll() is None:
                    os.utime(lockfile, None)
                    time.sleep(interval)

                if p.poll() != 3:
                    if os.path.exists(lockfile):
                        os.unlink(lockfile)
                    sys.exit(p.poll())
        except KeyboardInterrupt:
            pass
        finally:
            if os.path.exists(lockfile):
                os.unlink(lockfile)
        return

    def signal_handler(signal, frame):
        if not bgcheck.status:
            bgcheck.status = 'exit'
        bgcheck.join()
        if bgcheck.status == 'reload':
            # 子进程主动退出
            sys.exit(3)

    if os.environ.get('GUBED_APP'):
        lockfile = os.environ.get('GUBED_LOCKFILE')
        bgcheck = FileCheckerThread(lockfile, interval) # 4
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

        for module in list(sys.modules.values()):
            path = getattr(module, '__file__', '')
            if path[-4:] in ('.pyo', '.pyc'):
                path = path[:-1]
            if path and os.path.exists(path):
                files[path] = mtime(path)

        while not self.status:
            if not os.path.exists(self.lockfile)\
            or mtime(self.lockfile) < time.time() - self.interval - 5:
                self.status = 'error'
                thread.interrupt_main()
            # 检测每个文件的修改时间，若修改则向主线程发出 KeyboardInterrupt
            # 结束主线程中的 with 语句
            for path, lmtime in list(files.items()):
                if not os.path.exists(path) or mtime(path) > lmtime:
                    self.status = 'reload'
                    thread.interrupt_main()
                    break
            time.sleep(self.interval)
