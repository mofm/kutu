import logging
import ctypes
import ctypes.util
from pathlib import Path

from .variables import SYSCALL_NUM_GETPID, SYSCALL_NUM_CLONE

logger = logging.getLogger(__name__)

libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)


def mount(source: Path, target: Path, fstype, flags, data):
    if fstype is not None:
        fstype = fstype.encode('utf-8')
    if data is not None:
        data = data.encode('utf-8')
    if libc.mount(str(source).encode('utf-8'), str(target).encode('utf-8'), fstype, flags, data) != 0:
        raise OSError(ctypes.get_errno(), "Mount failed")


def umount(target: Path):
    return umount2(target, 0)


def umount2(target: Path, flags: int):
    if libc.umount2(str(target).encode('utf-8'), flags) != 0:
        raise OSError(ctypes.get_errno(), "Failed to unmount directory: {}; flags={}".format(target, flags))


def get_all_mounts():
    with Path("/proc/self/mounts").open('rb') as f:
        mounts = []
        for line in f:
            mp = line.split(b' ')[1]
            # unicode_escape is necessary because moutns with special characters are
            # represented with octal escape codes in 'mounts'
            mounts.append(Path(mp.decode('unicode_escape')))
    return mounts


def is_mount_point(path: Path):
    # os.path.ismount does not properly detect bind mounts
    return path.absolute() in get_all_mounts()


def unshare(flags):
    if libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), "unshare failed")


def setns(fd, flags):
    if libc.setns(fd, flags) != 0:
        raise OSError(ctypes.get_errno(), "setns failed")


def pivot_root(new_root: Path, old_root: Path):
    if libc.pivot_root(str(new_root).encode('utf-8'), str(old_root).encode('utf-8')) != 0:
        raise OSError(ctypes.get_errno(), "pivot_root failed")


def clone(flags, stack=0):
    syscall = libc.syscall
    syscall.restype = ctypes.c_int
    syscall.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_int)
    result = syscall(SYSCALL_NUM_CLONE, flags, stack)
    if result < 0:
        raise OSError(abs(result), "clone failed")
    return result


def non_caching_getpid():
    # libc caches the return value of getpid, and does not refresh this
    # cache, if we call syscalls (e.g. clone) by hand.
    syscall = libc.syscall
    syscall.restype = ctypes.c_int
    syscall.argtypes = (ctypes.c_int,)
    result = syscall(SYSCALL_NUM_GETPID)
    if result < 0:
        raise OSError(abs(result), "getpid failed")
    return result
