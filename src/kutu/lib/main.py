import argparse
import logging
import sys

from .output import nprint
from .. import kutu, __version__
from .usage import kutuctl_usage

logger = logging.getLogger(__name__)


no_args = {
    "usage": {
        "aliases": ["use"],
        "help": "Display this usage information and exit",
    },
    "version": {
        "aliases": ["v"],
        "help": "Output version information and exit",
    },
}


def parser_opts():
    """
    Common parser function
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    for myopt, kwargs in no_args.items():
        sargs = [myopt]
        sp = subparsers.add_parser(*sargs, **kwargs)
        sp.set_defaults(func=myopt)

    # bootstrap arguments
    sp = subparsers.add_parser("bootstrap",
                               help="Bootstrap a container from package servers",
                               )
    sp.add_argument("name")
    sp.add_argument("dist")
    sp.add_argument("version", nargs="?")
    sp.set_defaults(func="bootstrap")

    # image positional arguments
    sp = subparsers.add_parser("image", help="Manages Images")
    img_sub = sp.add_subparsers()
    # list positional args
    img_ls = img_sub.add_parser("list", aliases=["ls"], help="List Images")
    img_ls.set_defaults(func="img_list")
    # remove positional args
    img_rm = img_sub.add_parser("remove", aliases=["rm"], help="Remove Image")
    img_rm.add_argument("name", nargs="+")
    img_rm.set_defaults(func="img_remove")

    vargs = parser.parse_args()
    return vargs


class KtctlCmd(object):
    """
    KtctlCmd object
    """

    def __init__(self):
        self.cmd = None
        self.resp_string = None

    def action(self, args):
        """
        Calls the function
        """
        if self.cmd is not None:
            return False

        self.cmd = args['func']
        del args['func']
        self.resp_string = self.run_action(self.cmd, args)

        return True

    def run_action(self, cmd, args):
        """
        Run the function from _nspctl.py
        """
        cmd = cmd.lstrip("-").replace("-", "_")
        method = getattr(kutu, cmd)
        result = method(**args)
        fancy_result = nprint(result)

        return fancy_result

    def get_result(self):
        """
        Returns the response
        """
        if self.resp_string is None:
            raise Exception("Call action function first")

        return self.resp_string


def ktctl_main(args=None):
    """
    command arguments (default: usage)
    """
    if args is None:
        args = sys.argv[1:]

    args = parser_opts()
    args_map = vars(args)

    if not args_map or args_map['func'] in ('usage', None):
        kutuctl_usage()
    elif args_map['func'] == "version":
        print(__version__ + "\n")
    else:
        nsp = KtctlCmd()
        nsp.action(args_map)
        rev = nsp.get_result()
        print(rev)
