import fcntl
import errno


class LockFile(object):
    """
    Locks file via fcntl calls
    """
    def __init__(self, path):
        """
        default and mandatory arguments
        """
        self.path = path
        self.pidfile = None

    def lockfile(self):
        """
        Locks file with fcntl calls
        """
        lock_mode = fcntl.LOCK_EX
        while True:
            try:
                pidf = open(self.path, "r")
                while True:
                    try:
                        fcntl.flock(pidf, lock_mode)
                        break
                    except IOError as exc:
                        if exc.errno in (errno.EACCES, errno.EAGAIN):
                            raise Exception("File already locked: {}".format(exc))
                        else:
                            raise Exception(str(exc))
                pidf.flush()
                self.pidfile = pidf
                break
            except IOError as exc:
                raise Exception("Operation failed while locking: {}".format(exc))

    def release(self):
        """
        Release locked the file
        """
        if self.pidfile is not None:
            self.pidfile.close()

    def is_locked(self):
        """
        Check if the file is locked by other process
        """
        try:
            with open(self.path, "r") as pidf:
                try:
                    fcntl.flock(pidf, fcntl.LOCK_EX)
                    return False
                except IOError as exc:
                    if exc.errno in (errno.EACCES, errno.EAGAIN):
                        return True
                    else:
                        raise
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                return False
            else:
                raise
