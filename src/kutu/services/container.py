from ..lib.daemon import Daemon
from ..lib.contrun import ContainerContext


conenv = {"PATH": "/bin:/usr/bin:/sbin:/usr/sbin:/opt/bin:/usr/local/bin:/usr/local/sbin"}


class ContainerService(Daemon):
    def __init__(self, rootdir, pidfile, cmd=''):
        self.rootdir = rootdir
        self.cmd = cmd
        super().__init__(pidfile)

    def run(self):
        with ContainerContext(self.rootdir) as container:
            container.run(self.cmd, env=conenv)
