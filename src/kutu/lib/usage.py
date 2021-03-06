from .output import turquoise, green, yellow


def kutuctl_usage():
    print(yellow("nspctl:") + " management tool for systemd-nspawn containers")
    print(yellow("Synopsis:"))
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("arguments")
        + " ] [ "
        + green("options")
        + " ] [ "
        + turquoise("container name")
        + " | "
        + turquoise("URL")
        + " | "
        + turquoise("distribution")
        + " ] [ ... ]"
    )
    print(yellow("Usage:"))
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("info")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("list")
        + " ] [ "
        + green("list-running")
        + " ] [ "
        + green("list-stopped")
        + " ] [ "
        + green("list-all")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("start")
        + " | "
        + green("stop")
        + " | "
        + green("reboot")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("poweroff")
        + " | "
        + green("terminate")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("enable")
        + " | "
        + green("disable")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("shell")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("remove")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("copy-to")
        + " ] [ "
        + turquoise("container name")
        + " ] [ "
        + green("Host Path")
        + " ] [ "
        + green("Container Path")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("rename")
        + " ] [ "
        + turquoise("container name")
        + " ] [ "
        + turquoise("new container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("exec")
        + " ] [ "
        + turquoise("container name")
        + " ] [ "
        + turquoise("command")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("--help")
        + " | "
        + green("-h")
        + " ] "
    )
    print(yellow("Container Operations:"))
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("pull-raw")
        + " | "
        + green("pull-tar")
        + " | "
        + green("pull-dkr")
        + " ] [ "
        + turquoise("URL")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("import-raw")
        + " | "
        + green("import-tar")
        + " ] [ "
        + turquoise("image path")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("import-fs")
        + " ] [ "
        + turquoise("directory path")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("bootstrap")
        + " ] [ "
        + turquoise("container name")
        + " ] [ "
        + turquoise("debian")
        + " | "
        + turquoise("ubuntu")
        + " | "
        + turquoise("arch")
        + " ] [ "
        + green("version")
        + " ] "
    )
    print(yellow("Shortcuts:"))
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("(ls, lsr, list) -> list-running")
        + " ] [ "
        + green("lss -> list-stopped")
        + " ] [ "
        + green("lsa -> list-all")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("en -> enable")
        + " ] [ "
        + green("dis -> disable")
        + " ] [ "
        + green("rm -> remove")
        + "] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("sh -> shell")
        + " ] [ "
        + turquoise("container name")
        + " ] "
    )
    print(
        "   "
        + turquoise("nspctl")
        + " [ "
        + green("cpt -> copy-to")
        + " ] [ "
        + turquoise("container name")
        + " ] [ "
        + turquoise("source")
        + " ] [ "
        + turquoise("destination")
        + " ] "
    )
    print()
    print("   For more help: https://github.com/mofm/kutu \n")
