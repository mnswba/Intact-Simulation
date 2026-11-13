"""Portable host locking and background-process control; not a CAD sandbox."""
import os
import subprocess
import time

if os.name != 'nt':
    import fcntl as file_lock
else:
    import msvcrt

    class file_lock:
        LOCK_EX, LOCK_NB, LOCK_UN = 2, 4, 8

        @staticmethod
        def flock(stream, flags):
            fd = stream if isinstance(stream, int) else stream.fileno()
            while True:
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK if flags & 8 else msvcrt.LK_NBLCK, 1)
                    return
                except OSError as exc:
                    if flags & 8:raise
                    if flags & 4:raise BlockingIOError('The file is locked by another process.') from exc
                    time.sleep(.05)


def background_options():
    return {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}


def process_matches(pid, module):
    if os.name == 'nt':
        import psutil
        try:return module in psutil.Process(pid).cmdline()
        except (psutil.Error, ValueError):return False
    from pathlib import Path
    try:return module.encode() in (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
    except OSError:return False


def terminate_tree(process, force=False):
    if process.poll() is not None:return
    if os.name == 'nt':
        import psutil
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                try:child.kill() if force else child.terminate()
                except psutil.Error:pass
            parent.kill() if force else parent.terminate()
        except psutil.NoSuchProcess:pass
    else:
        import signal
        try:os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
        except ProcessLookupError:pass
