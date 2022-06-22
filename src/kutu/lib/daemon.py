import os
import sys
import time
import atexit
import signal
import logging

from .lockfile import LockFile

logger = logging.getLogger(__name__)


class Daemon:
    """
    A generic daemon class.
    Usage: subclass the Daemon class and override the run() method
    """

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.lckfile = LockFile(self.pidfile)

    def daemonize(self):
        """
        do the UNIX double-fork magic
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as exc:
            logger.error("fork #1 failed: %d (%s)\n" % (exc.errno, exc.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as exc:
            logger.error("fork #2 failed: %d (%s)\n" % (exc.errno, exc.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        pid = str(os.getpid())
        try:
            with open(os.open(self.pidfile, os.O_CREAT | os.O_WRONLY, 0o644), 'w') as f:
                f.write("%s\n" % pid)
            self.lckfile.lockfile()
        except OSError as exc:
            logger.error("pid file didn't create correctly: %s", exc)
            sys.exit(1)

    def delpid(self):
        self.lckfile.release()
        os.remove(self.pidfile)

    def _signal_handler(self, signum, frame):
        self.delpid()
        os.kill(pid, signum)

    def start(self):
        """
        Start the daemon
        """
        # Handle Signal
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            logger.warning(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()
        atexit.register(self.delpid)

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            logger.warning(message % self.pidfile)
            # not an error in a restart
            return

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as exc:
            err = str(exc)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    # self.lfile.release()
                    # os.remove(self.pidfile)
                    self.delpid()
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
