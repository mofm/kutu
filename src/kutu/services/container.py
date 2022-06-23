from ..lib.daemon import Daemon
from ..lib.mount import OverlayfsMountContext
from ..lib.contrun import ContainerContext


conenv = {"PATH": "/bin:/usr/bin:/sbin:/usr/sbin:/opt/bin:/usr/local/bin:/usr/local/sbin"}


class ContainerStart(Daemon):
    def __init__(self, rootdir, imgdir, pidfile, cmd=''):
        self.rootdir = rootdir
        self.imgdir = imgdir
        self.cmd = cmd
        super().__init__(pidfile)

    def run(self):
        with OverlayfsMountContext([self.imgdir], self.rootdir + "/upperdir",
                                   self.rootdir + "/workdir", self.rootdir + "/merged"):
            with ContainerContext(self.rootdir + "/merged") as container:
                container.run(self.cmd, env=conenv)


class ContainerStop(Daemon):
    def __init__(self, pidfile):
        super().__init__(pidfile)
