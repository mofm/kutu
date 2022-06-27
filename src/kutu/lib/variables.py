from collections import namedtuple
from pathlib import Path


MS_RDONLY = 0x00000001
MS_NOSUID = 0x00000002
MS_NODEV = 0x00000004
MS_NOEXEC = 0x00000008
MS_REMOUNT = 0x00000020
MS_NOATIME = 0x00000400
MS_NODIRATIME = 0x00000800
MS_BIND = 0x00001000
MS_MOVE = 0x00002000
MS_REC = 0x00004000
MS_PRIVATE = 0x00040000
MS_SLAVE = 0x00080000
MS_SHARED = 0x00100000
MS_STRICTATIME = 0x01000000

CLONE_FS = 0x00000200
CLONE_FILES = 0x00000400
CLONE_NEWNS = 0x00020000
CLONE_NEWUTS = 0x04000000
CLONE_NEWIPC = 0x08000000
CLONE_NEWUSER = 0x10000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
CLONE_NEWCGROUP = 0x02000000

SYSCALL_NUM_CLONE = 56
SYSCALL_NUM_GETPID = 39

MNT_DETACH = 2

Mount = namedtuple('Mount', ['destination', 'type', 'source', 'flags', 'options'])
DeviceNode = namedtuple('DeviceNode', ['name', 'major', 'minor'])
BindMount = namedtuple('BindMount', ['source', 'destination', 'readonly'])

NAMESPACES = {
    "pid": CLONE_NEWPID,
    "cgroup": CLONE_NEWCGROUP,
    "ipc": CLONE_NEWIPC,
    "uts": CLONE_NEWUTS,
    "mnt": CLONE_NEWNS,
    "net": CLONE_NEWNET,
}

CONTAINER_MOUNTS = [
    Mount(
        destination=Path("/proc"),
        type="proc",
        source="proc",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=None,
    ),
    Mount(
        destination=Path("/proc/sys"),
        type=None,
        source=Path("/proc/sys"),
        flags=MS_BIND,
        options=None,
    ),
    Mount(
        destination=Path("/proc/sys/net"),
        type=None,
        source=Path("/proc/sys/net"),
        flags=MS_BIND,
        options=None,
    ),
    Mount(
        destination=Path("/proc/sys"),
        type=None,
        source=None,
        flags=MS_BIND | MS_RDONLY | MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_REMOUNT,
        options=None,
    ),
    Mount(
        destination=Path("/dev"),
        type="tmpfs",
        source="tmpfs",
        flags=MS_NOSUID | MS_STRICTATIME,
        options=[
            "mode=755",
            "size=4m",
            "nr_inodes=1m",
        ],
    ),
    Mount(
        destination=Path("/dev/pts"),
        type="devpts",
        source="devpts",
        flags=MS_NOSUID | MS_NOEXEC,
        options=[
            "newinstance",
            "ptmxmode=0666",
            "mode=0620",
            "gid=5",
        ],
    ),
    Mount(
        destination=Path("/dev/shm"),
        type="tmpfs",
        source="shm",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=[
            "mode=1777",
            "size=10%",
            "nr_inodes=400k",
        ],
    ),
    Mount(
        destination=Path("/dev/mqueue"),
        type="mqueue",
        source="mqueue",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV,
        options=None,
    ),
    Mount(
        destination=Path("/sys"),
        type="sysfs",
        source="sysfs",
        flags=MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY,
        options=None,
    ),
    Mount(
        destination=Path("/run"),
        type="tmpfs",
        source="tmpfs",
        flags=MS_NOSUID | MS_STRICTATIME | MS_NODEV,
        options=[
            "mode=755",
            "size=20%",
            "nr_inodes=800k"
        ],
    ),
    Mount(
        destination=Path("/tmp"),
        type="tmpfs",
        source="tmpfs",
        flags=MS_NOSUID | MS_STRICTATIME | MS_NODEV,
        options=[
            "mode=1777",
            "size=10%",
            "nr_inodes=400k",
        ],
    ),
]

INACCESSIBLE_MOUNTS = [
    "/proc/kallsyms",
    "/proc/kcore",
    "/proc/keys",
    "/proc/sysrq-trigger",
    "/proc/timer_list"
]

READONLY_MOUNTS = [
        "/proc/acpi",
        "/proc/apm"
        "/proc/asound",
        "/proc/bus",
        "/proc/fs",
        "/proc/irq",
        "/proc/scsi"
]

CONTAINER_DEVICE_NODES = [
    DeviceNode(
        name="null",
        major=1,
        minor=3,
    ),
    DeviceNode(
        name="zero",
        major=1,
        minor=5,
    ),
    DeviceNode(
        name="full",
        major=1,
        minor=7,
    ),
    DeviceNode(
        name="tty",
        major=5,
        minor=0,
    ),
    DeviceNode(
        name="random",
        major=1,
        minor=8,
    ),
    DeviceNode(
        name="urandom",
        major=1,
        minor=9,
    ),
]

HOST_NETWORK_BIND_MOUNTS = [
    BindMount(
        source=Path('/etc/resolv.conf'),          # path on host machine
        destination=Path('/etc/resolv.conf'),     # path in container
        readonly=True,
    ),
]
