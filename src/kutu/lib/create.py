import json
import logging
import os
import signal
import stat
import subprocess
import sys
from socket import sethostname
from pathlib import Path

from kutu.lib.libc import unshare, mount, umount2, non_caching_getpid, pivot_root, is_mount_point
from kutu.lib.variables import *
from kutu.utils.genhostname import gen_hostname

logger = logging.getLogger(__name__)

HOSTNAME = gen_hostname(8)


class PID1:
    def __init__(self, root_dir, control_read, control_write, isolate_networking, bind_mounts):
        self.control_read = control_read
        self.control_write = control_write
        self.root_dir = Path(root_dir).resolve()
        self.isolate_networking = isolate_networking
        self.bind_mounts = self.convert_bind_mounts_parameter(bind_mounts)
        self.loop_devices = list(self.get_loop_devices())

    @classmethod
    def convert_bind_mounts_parameter(cls, bind_mounts):
        result = []
        for source, destination, read_only in bind_mounts:
            source = Path(source)
            destination = Path(destination)
            if destination.is_absolute():
                destination = destination.relative_to("/")
            result.append(BindMount(source, destination, read_only))
        return result

    def enable_zombie_reaping(self):
        # We are pid 1, so we have to take care of orphaned processes
        # Interestingly, SIG_IGN is the default handler for SIGCHLD,
        # but this way we signal to the kernel that we will not call waitpid
        # and get rid of zombies automatically
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    @classmethod
    def create_mount_target(cls, source, destination):
        if source.is_file():
            if destination.is_symlink():
                destination.unlink()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.touch()
        else:
            destination.mkdir(parents=True, exist_ok=True)

    def create_bind_mounts(self):
        for source, relative_destination, read_only in self.bind_mounts:
            destination = self.root_dir.joinpath(relative_destination)
            self.create_mount_target(source, destination)
            mount(source, destination, None, MS_BIND, None)
            if read_only:
                # "Read-only bind mounts" are actually an illusion, a special feature of the kernel,
                # which is why we have to make the bind mount read-only in a separate call.
                # See https://lwn.net/Articles/281157/
                flags = MS_REMOUNT | MS_BIND | MS_RDONLY
                mount(Path(), destination, None, flags, None)

    def setup_root_mount(self):
        # SLAVE means that mount events will get inside the container, but
        # mounting something inside will not leak out.
        # Use PRIVATE to not let outside events propagate in
        mount(Path("none"), Path("/"), None, MS_REC | MS_SLAVE, None)
        self.create_bind_mounts()
        if not is_mount_point(self.root_dir):
            mount(self.root_dir, self.root_dir, None, MS_BIND, None)
        old_root_dir = self.root_dir.joinpath('old_root')
        old_root_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(str(self.root_dir))
        pivot_root(Path('.'), Path('old_root'))
        os.chroot('.')

    def mount_defaults(self):
        for m in CONTAINER_MOUNTS:
            options = None
            if m.options:
                options = ",".join(m.options)
            m.destination.mkdir(parents=True, exist_ok=True)
            mount(m.source, m.destination, m.type, m.flags, options)

    def inaccessible_mounts(self):
        for m in INACCESSIBLE_MOUNTS:
            mount(Path("/dev/null"), m, None, MS_BIND, None)
            mount(None, m, None, MS_BIND | MS_RDONLY | MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_REMOUNT, None)

    def readonly_mounts(self):
        for m in READONLY_MOUNTS:
            if Path(m).exists():
                mount(m, m, None, MS_BIND, None)
                mount(None, m, None, MS_BIND | MS_RDONLY | MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_REMOUNT, None)

    def create_device_node(self, name, major, minor, mode, *, is_block_device=False):
        if is_block_device:
            device_type = stat.S_IFBLK
        else:
            device_type = stat.S_IFCHR
        nodepath = Path("/dev", name)
        os.mknod(str(nodepath), mode=device_type, device=os.makedev(major, minor))
        # A separate chmod is necessary, because mknod (undocumentedly) takes umask into account when creating
        nodepath.chmod(mode=mode)

    def create_default_dev_nodes(self):
        for d in CONTAINER_DEVICE_NODES:
            if d.name == "console":
                self.create_device_node(d.name, d.major, d.minor, 0o600)
            else:
                self.create_device_node(d.name, d.major, d.minor, 0o666)

    def create_symlink_devices(self):
        try:
            # create ptmx symlink
            os.symlink("pts/ptmx", "/dev/ptmx")
            os.symlink("pts/0", "/dev/console")
            os.symlink("/proc/self/fd", "/dev/fd")
            os.symlink("/proc/self/fd/0", "/dev/stdin")
            os.symlink("/proc/self/fd/1", "/dev/stdout")
            os.symlink("/proc/self/fd/2", "/dev/stderr")
            os.symlink("/proc/kcore", "/dev/core")
        except OSError as exc:
            raise Exception("Failed to create symlink to devices: {}".format(exc))

    def umount_old_root(self):
        umount2('/old_root', MNT_DETACH)
        os.rmdir('/old_root')

    def create_namespaces(self):
        unshare_flags = 0
        for name, flag in NAMESPACES.items():
            if flag == CLONE_NEWPID:
                continue
            if flag == CLONE_NEWNET and not self.isolate_networking:
                continue
            if Path('/proc/self/ns', name).exists():
                unshare_flags = unshare_flags | flag
            else:
                logger.warning("Namespace type {} not supported on this system".format(name))
        unshare(unshare_flags)

    def run(self):
        if non_caching_getpid() != 1:
            raise ValueError("We are not actually PID1, exiting for safety reasons")

        # codecs are loaded dynamically, and won't work when we remount root
        make_sure_codecs_are_loaded = b'a'.decode('unicode_escape')  # NOQA: F841 local variable 'make_sure_codecs_are_loaded' is assigned to but never used
        os.setsid()
        self.enable_zombie_reaping()
        self.create_namespaces()
        self.setup_root_mount()
        self.mount_defaults()
        self.create_default_dev_nodes()
        self.create_symlink_devices()
        self.inaccessible_mounts()
        self.readonly_mounts()
        self.umount_old_root()
        sethostname(HOSTNAME)

        os.write(self.control_write, b"RDY")
        logger.debug("Container started")
        # this will return when the pipe is closed
        # E.g. the outside control process died before killing us
        os.read(self.control_read, 1)
        logger.debug("Control pipe closed, stopping")
        return 0

    # NOTE: use only before create_namespaces()
    def get_loop_devices(self):
        for loop_path in Path('/dev').glob('loop[0-9]*'):
            major, minor = divmod(os.stat(str(loop_path)).st_rdev, 256)
            if major == 7:  # it's a loop device
                yield DeviceNode(name=loop_path.name, major=major, minor=minor)


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    logger.setLevel(args.pop("loglevel"))
    pid1 = PID1(**args)
    sys.exit(pid1.run())
