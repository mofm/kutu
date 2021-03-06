import abc
from json import JSONEncoder
from pathlib import Path
import logging

from .libc import mount, umount, umount2
from .variables import MS_BIND, MNT_DETACH, MS_REMOUNT, MS_RDONLY

logger = logging.getLogger(__name__)


class PathEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


class MountContext(abc.ABC):
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

    def umount(self):
        logger.debug("Unmounting {path}".format(path=self.destination))
        try:
            umount(self.destination)
        except OSError:
            logger.warning("Failed to umount {path}, detaching instead".format(path=self.destination))
            umount2(self.destination, MNT_DETACH)

    @abc.abstractmethod
    def get_mount_parameters(self):
        pass

    def mount(self):
        fstype, flags, options = self.get_mount_parameters()
        mount(self.source, self.destination, fstype, flags, options)

    def __enter__(self):
        self.mount()
        return self

    def __exit__(self, type, value, traceback):
        self.umount()


class BindMountContext(MountContext):
    def __init__(self, source, destination, read_only=False):
        super().__init__(source, destination)
        self.read_only = read_only

    def get_mount_parameters(self):
        return None, MS_BIND, None

    def mount(self):
        super().mount()
        if self.read_only:
            mount(Path(), self.destination, None, MS_REMOUNT | MS_BIND | MS_RDONLY, None)


class OverlayfsMountContext(MountContext):
    def __init__(self, ro_dirs, rw_dir, work_dir, destination):
        super().__init__("overlay", destination)
        self.ro_dirs = ro_dirs
        self.rw_dir = rw_dir
        self.work_dir = work_dir

    def get_mount_parameters(self):
        options_string = 'lowerdir={lowerdir},upperdir={upperdir},workdir={workdir}'.format(
            lowerdir=':'.join([str(path) for path in self.ro_dirs]),
            upperdir=self.rw_dir,
            workdir=self.work_dir
        )
        return "overlay", 0, options_string
