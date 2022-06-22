import functools
import os
import errno
import shutil
import re
import tempfile
import json
from time import strftime, localtime
import shlex
import logging

from .utils.kwargs import clean_kwargs, invalid_kwargs
from .utils.user import get_uid
from .utils.path import which
from .utils.platform import get_arch
from .utils.getfile import file_get
from .utils.tar import tar_extract
from .utils.checksum import checksum_url, parse_checksum, verify_all
from .utils.cmd import run_cmd
from .lib.funcutils import alias_function
from .services.container import ContainerService
from .lib.contrun import ContainerContext

logger = logging.getLogger(__name__)


# def _ensure_exists(wrapped):
#     """
#     Decorator to ensure that the named container exists
#     """
#     @functools.wraps(wrapped)
#     def check_exists(name, *args, **kwargs):
#         if not exists(name):
#             raise Exception("Container '{}' does not exist".format(name))
#         return wrapped(name, *args, **clean_kwargs(**kwargs))
#
#     return check_exists


def _check_useruid(wrapped):
    """
    Decorator check to user has root privileges
    """
    @functools.wraps(wrapped)
    def check_uid(*args, **kwargs):
        if get_uid() != 0:
            raise Exception("This command requires root privileges!")
        return wrapped(*args, **clean_kwargs(**kwargs))

    return check_uid


def _img_root(name="", all_roots=False):
    """
    Return the image root directory
    """
    userhome = os.getenv("HOME")
    homedir = os.path.join(userhome, '.kutu/images')
    if all_roots:
        return [
            os.path.join(x, name)
            for x in ("/var/lib/kutu/images", homedir)
        ]
    else:
        return os.path.join("/var/lib/kutu/images", name)


def _cont_root(name="", all_roots=False):
    """
    Return the container root directory
    """
    userhome = os.getenv("HOME")
    homedir = os.path.join(userhome, '.kutu/containers')
    if all_roots:
        return [
            os.path.join(x, name)
            for x in ("/var/lib/kutu/containers", homedir)
        ]
    else:
        return os.path.join("/var/lib/kutu/containers", name)


def _make_images_root(name):
    """
    Make the image root directory
    """
    path = _img_root(name)
    if os.path.exists(path):
        raise Exception("Image {} already exists".format(name))
    else:
        try:
            os.makedirs(path)
            return path
        except OSError as exc:
            raise Exception(
                "Unable to make image root directory {}: {}".format(name, exc)
            )


def _make_container_root(name):
    """
    Make the container root directory
    """
    path = _cont_root(name)
    if os.path.exists(path):
        raise Exception("Container {} already exists.".format(name))
    else:
        ofs_subs = ['upperdir', 'workdir', 'merged']
        try:
            os.makedirs(path)
            for folder in ofs_subs:
                os.makedirs(os.path.join(name, folder), exist_ok=True)

            return path
        except OSError as exc:
            raise Exception(
                "Unable to make container root directory {}: {}".format(name, exc)
            )


def _pid(name=""):
    """
    Return container pid file
    """
    pidfile = ""
    if name:
        pidfile = name + ".pid"

    return os.path.join("/var/run/kutu/", pidfile)


def _build_failed(dest, name):
    """
    build failed function
    """
    try:
        shutil.rmtree(dest)
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise Exception(
                "Unable to cleanup container root directory {}".format(dest)
            )
    raise Exception("Container {} failed to build".format(name))


def _add_img_json(name, imgbase, version):
    """
    adds new image to json file
    """
    new_img = {
        "ImageName": name,
        "ImageBase": imgbase,
        "Version": version,
        "CreatedTime": strftime("%Y-%m-%d %H:%M:%S", localtime())
    }
    try:
        with open(os.path.join(_img_root(), "images.json"), "r+") as f:
            json_data = json.load(f)
            json_data["images"].append(new_img)
            f.seek(0)
            json.dump(json_data, f, indent=4, separators=(", ", ": "), sort_keys=True)
    except OSError as exc:
        raise Exception("Image {} failed to add to json file: {}".format(name, exc))


def _bootstrap_alpine(name, **kwargs):
    """
    Boostrap an Alpine Linux container
    """
    imgbase = "Alpine Linux"
    releases = [
        "v3.13",
        "v3.14",
        "v3.15",
        "v3.16",
        "latest-stable",
    ]

    version = kwargs.get("version", False)
    if not version or version == "latest-stable":
        version = max(releases)

    if version not in releases:
        raise Exception(
            'Unsupported Alpine version "{}". '
            'Only "latest-stable" or "v3.13" and newer are supported'.format(version)
        )
    dest = _make_images_root(name)
    mirror = "https://dl-cdn.alpinelinux.org/alpine/"
    arch = get_arch()
    base_url = mirror + version + "/releases/" + arch + "/"
    temp_dir = tempfile.mkdtemp()

    def _getlastversion():
        reason = "unknown"
        yaml = "latest-releases.yaml"
        yaml_url = base_url + yaml
        fetch_yaml = file_get(yaml_url, temp_dir)
        if fetch_yaml == 0:
            with open(os.path.join(temp_dir, yaml), "r") as f:
                data = f.read()
        else:
            raise Exception("Latest release is not available")
        regex = r"alpine-minirootfs-.+"
        matches = re.findall(regex, data, re.MULTILINE)
        if matches:
            return True, matches[0]
        else:
            return False, reason

    try:
        # get last alpine release version
        result = _getlastversion()
        if result[0]:
            rootfs_version = result[1]
        else:
            raise Exception("Rootfs version not found")

        rootfs_url = base_url + rootfs_version
        # get checksum url for data integrity
        sums_url = checksum_url(rootfs_version, "SHA256")
        fetch_rootfs = file_get(rootfs_url, temp_dir)
        if fetch_rootfs == 0:
            for file in sums_url:
                new_url = base_url + file
                conn = file_get(new_url, temp_dir)
                if conn == 0:
                    sum_file = file
            my_dict = {}
            chksum = parse_checksum(rootfs_version, os.path.join(temp_dir, sum_file))
            my_dict.update({"SHA256": chksum})
            temp_path = os.path.join(temp_dir, rootfs_version)
            # verify file checksum
            verify = verify_all(temp_path, my_dict)
            if verify[0] is True:
                tar_extract(temp_path, dest)
            else:
                raise Exception("'{}': The checksum format is invalid".format(rootfs_version))
            _add_img_json(name, imgbase, version)
    except Exception as exc:
        _build_failed(dest, name)
        raise Exception(str(exc)) from None
    finally:
        shutil.rmtree(temp_dir)

    return True


def _debootstrap(name, version, imgbase):
    """
    Common deboostrap function
    """
    if not which("debootstrap"):
        raise Exception(
            "debootstrap not found, is the debootstrap package installed?"
        )
    try:
        dest = _make_images_root(name)
        cmd = "debootstrap --include=systemd-container {} {}".format(version, dest)
        ret = run_cmd(cmd, is_shell=True)

        if ret["returncode"] != 0:
            raise Exception("Deboostrap failed while installing {} image".format(name))

        _add_img_json(name, imgbase, version)
        return ret["stdout"]
    except Exception as exc:
        _build_failed(dest, name)
        raise Exception(str(exc)) from None


def _bootstrap_debian(name, **kwargs):
    """
    Bootstrap a Debian Linux container
    """
    imgbase = "Debian Linux"
    version = kwargs.get("version", False)
    if not version:
        version = "stable"

    releases = [
        "stretch",
        "buster",
        "bullseye",
        "stable",
    ]
    if version not in releases:
        raise Exception(
            'Unsupported Debian version "{}". '
            'Only "stable" or "stretch" and newer are supported'.format(version)
        )
    return _debootstrap(name, version, imgbase)


def _bootstrap_ubuntu(name, **kwargs):
    """
    Bootstrap a Ubuntu Linux container
    """
    imgbase = "Ubuntu Linux"
    version = kwargs.get("version", False)
    if not version:
        version = "focal"

    releases = [
        "bionic",
        "focal",
        "jammy",
    ]
    if version not in releases:
        raise Exception(
            'Unsupported Ubuntu version "{}". '
            '"bionic" and newer are supported'.format(version)
        )
    return _debootstrap(name, version, imgbase)


@_check_useruid
def bootstrap_container(name, dist=None, version=None):
    """
    Bootstrap a container from package servers
    """
    distro = [
        "debian",
        "ubuntu",
        "alpine",
    ]

    if dist not in distro and dist is None:
        raise Exception(
            'Unsupported distribution "{}"'.format(dist)
        )
    try:
        return globals()["_bootstrap_{}".format(dist)](name, version=version)
    except KeyError:
        raise Exception('Unsupported distribution "{}"'.format(dist))


bootstrap = alias_function(bootstrap_container, "bootstrap")


def list_all():
    """
    Lists all kutu images
    """
    ret = ["Image Name\tImage Base\tVersion\tCreated Time"]
    img_json = os.path.join(_img_root(), "images.json")
    try:
        with open(img_json, 'r') as f:
            data = json.load(f)

        for i in data["images"]:
            ret.append("{}\t{}\t{}\t{}".format(i["ImageName"], i["ImageBase"], i["Version"], i["CreatedTime"]))
        return ret
    except json.JSONDecodeError:
        raise Exception("'images.json' file decode failed")
    except IOError:
        raise Exception("'images.json' file could not be opened")


def remove(name):
    """
    Remove the named image
    """
    def _failed_remove(name, exc):
        raise Exception("Unable to remove image '{}': '{}'".format(name, exc))

    try:
        with open(os.path.join(_img_root(), "images.json"), "r+") as f:
            json_data = json.load(f)
            for i in json_data["images"]:
                if i["ImageName"] == name:
                    json_data["images"].remove(i)
            f.seek(0)
            json.dump(json_data, f, indent=4, separators=(", ", ": "), sort_keys=True)
            f.truncate()

        shutil.rmtree(os.path.join(_img_root(), name))
    except (OSError, json.JSONDecodeError) as exc:
        _failed_remove(name, exc)

    return True


# def list_running():
#     """
#     Lists running kutu containers
#     """
#     ret = []
#     piddir = _pid()
#     try:
#         for pidname in os.listdir(piddir):
#             if os.path.isfile(os.path.join(piddir, pidname)):
#                 ret.append(pidname.split('.')[0])
#     except OSError:
#         pass
#
#     return ret
#
#
# alias_list = alias_function(list_running, "list")
#
#
# def list_stopped():
#     """
#     Lists stopped kutu containers
#     """
#     return sorted(set(list_all()) - set(list_running()))
#
#
# def exists(name):
#     """
#     Return true if the named container exists
#     """
#     if name in list_all():
#         return True
#     else:
#         return False
#
#
# @_ensure_exists
# @_check_useruid
# def run(name, cmd):
#     """
#     Run the named kutu container with entry point command
#     """
#     entryo = shlex.split(cmd)
#     rootdir = _root(name)
#     piddir = _pid(name)
#     conservice = ContainerService(rootdir, piddir, entryo)
#     return conservice.start()
#
#
# @_ensure_exists
# @_check_useruid
# def kill(name):
#     """
#     Kill the named kutu container
#     """
#     rootdir = _root(name)
#     piddir = _pid(name)
#     conservice = ContainerService(rootdir, piddir)
#     return conservice.stop()
#
#
# @_ensure_exists
# def state(name):
#     """
#     Return the state of container (running or stopped)
#     """
#     if name in list_running():
#         return "Running"
#     else:
#         return "Stopped"
#
#
# @_ensure_exists
# @_check_useruid
# def remove(name, stop=False):
#     """
#     Remove the named kutu container
#     """
#     if not stop and state(name) != "Stopped":
#         raise Exception("Container is not stopped: {}".format(name))
#
#     def _failed_remove(name, exc):
#         raise Exception("Unable to remove container {}: {}".format(name, exc))
#
#     try:
#         shutil.rmtree(os.path.join(_root(), name))
#     except OSError as exc:
#         _failed_remove(name, exc)
#
#     return True
#
#
# @_ensure_exists
# @_check_useruid
# def shell(name):
#     """
#     login the interactive shell in the container
#     """
#     if state(name) != "Running":
#         raise Exception("Container is not running: {}".format(name))
#
#     rootdir = _root(name)
#     with ContainerContext(rootdir) as container:
#         container.interactive_shell()
