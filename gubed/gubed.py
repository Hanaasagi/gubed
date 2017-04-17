# -*-coding:UTF-8-*-
import os
import sys
import time
import tempfile
import threading
import thread
import subprocess
import signal

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
            # pass
            print('\nUser Exit[<Ctrl-C>]')
        finally:
            if os.path.exists(lockfile):
                os.unlink(lockfile)
        # is here need sys.exit???
        # return
        sys.exit()

    def signal_handler(signal, frame):
        if not bgcheck.status:
            bgcheck.status = 'exit'
        bgcheck.join()
        if bgcheck.status == 'reload':
            # subprocess exit and send signal 3
            sys.exit(3)
        else:
            sys.exit(0)

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
