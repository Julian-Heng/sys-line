#!/usr/bin/env python3

""" Argument handling """

import argparse
import platform
import textwrap


def parse():
    """ Parse the program arguments """
    prefixes = ["B", "KiB", "MiB", "GiB", "TiB"]

    fmt = argparse.RawDescriptionHelpFormatter
    desc = "a simple status line generator"
    epilog = """
        list of prefixes:
            {}
    """.format(", ".join(prefixes))
    epilog = textwrap.dedent(epilog)

    ver = "%(prog)s ("

    if "__compiled__" in globals():
        ver = "{}Nuitka {}.{}.{}-{}, ".format(ver,
                                              __compiled__.major,
                                              __compiled__.minor,
                                              __compiled__.micro,
                                              __compiled__.releaselevel)

    ver = "{}{} {}, {})".format(ver,
                                platform.python_implementation(),
                                platform.python_version(),
                                " ".join(platform.python_build()))

    parser = argparse.ArgumentParser(description=desc, epilog=epilog,
                                     formatter_class=fmt)

    parser.add_argument("format")
    parser.add_argument("-v", "--version", action="version",
                        version=ver)

    groups = {
        "cpu": parser.add_argument_group("cpu"),
        "mem": parser.add_argument_group("memory"),
        "swap": parser.add_argument_group("swap"),
        "disk": parser.add_argument_group("disk"),
        "bat": parser.add_argument_group("bat"),
        "net": parser.add_argument_group("network"),
        "date": parser.add_argument_group("date"),
        "misc": parser.add_argument_group("misc")
    }

    groups["cpu"].add_argument("-cls", "--cpu-load-short",
                               action="store_true", default=False)
    groups["cpu"].add_argument("-cur", "--cpu-usage-round",
                               action="store", type=int, default=2,
                               metavar="int")
    groups["cpu"].add_argument("-ctr", "--cpu-temp-round",
                               action="store", type=int, default=1,
                               metavar="int")

    groups["mem"].add_argument("-mup", "--mem-used-prefix",
                               action="store", default="MiB",
                               choices=prefixes, metavar="prefix")
    groups["mem"].add_argument("-mtp", "--mem-total-prefix",
                               action="store", default="MiB",
                               choices=prefixes, metavar="prefix")
    groups["mem"].add_argument("-mur", "--mem-used-round",
                               action="store", type=int, default=0,
                               metavar="int")
    groups["mem"].add_argument("-mtr", "--mem-total-round",
                               action="store", type=int, default=0,
                               metavar="int")
    groups["mem"].add_argument("-mpr", "--mem-percent-round",
                               action="store", type=int, default=2,
                               metavar="int")

    groups["swap"].add_argument("-sup", "--swap-used-prefix",
                                action="store", default="MiB",
                                choices=prefixes, metavar="prefix")
    groups["swap"].add_argument("-stp", "--swap-total-prefix",
                                action="store", default="MiB",
                                choices=prefixes, metavar="prefix")
    groups["swap"].add_argument("-sur", "--swap-used-round",
                                action="store", type=int, default=0,
                                metavar="int")
    groups["swap"].add_argument("-str", "--swap-total-round",
                                action="store", type=int, default=0,
                                metavar="int")
    groups["swap"].add_argument("-spr", "--swap-percent-round",
                                action="store", type=int, default=2,
                                metavar="int")

    mut_group = groups["disk"].add_mutually_exclusive_group()
    mut_group.add_argument("-dd", "--disk", action="store",
                           metavar="disk")
    mut_group.add_argument("-dm", "--mount", action="store", default="/",
                           metavar="mount")

    groups["disk"].add_argument("-dsd", "--disk-short-dev",
                                action="store_true", default=False)
    groups["disk"].add_argument("-dup", "--disk-used-prefix",
                                action="store", default="GiB",
                                choices=prefixes, metavar="prefix")
    groups["disk"].add_argument("-dtp", "--disk-total-prefix",
                                action="store", default="GiB",
                                choices=prefixes, metavar="prefix")
    groups["disk"].add_argument("-dur", "--disk-used-round",
                                action="store", type=int, default=2,
                                metavar="int")
    groups["disk"].add_argument("-dtr", "--disk-total-round",
                                action="store", type=int, default=2,
                                metavar="int")
    groups["disk"].add_argument("-dpr", "--disk-percent-round",
                                action="store", type=int, default=2,
                                metavar="int")

    groups["bat"].add_argument("-bpr", "--bat-percent-round",
                               action="store", type=int, default=2,
                               metavar="int")

    groups["bat"].add_argument("-bppr", "--bat-power-round",
                               action="store", type=int, default=2,
                               metavar="int")

    groups["net"].add_argument("-ndp", "--net-download-prefix",
                               action="store", default="KiB",
                               choices=prefixes, metavar="prefix")
    groups["net"].add_argument("-nup", "--net-upload-prefix",
                               action="store", default="KiB",
                               choices=prefixes, metavar="prefix")
    groups["net"].add_argument("-nur", "--net-used-round",
                               action="store", type=int, default=2,
                               metavar="int")
    groups["net"].add_argument("-ntr", "--net-total-round",
                               action="store", type=int, default=2,
                               metavar="int")

    groups["date"].add_argument("-tdf", "--date-format",
                                action="store", type=str, default="%a, %d %h",
                                metavar="str")

    groups["date"].add_argument("-tf", "--time-format",
                                action="store", type=str, default="%H:%M",
                                metavar="str")

    groups["misc"].add_argument("-mvr", "--misc-volume-round",
                                action="store", type=int, default=0,
                                metavar="int")
    groups["misc"].add_argument("-msr", "--misc-screen-round",
                                action="store", type=int, default=0,
                                metavar="int")

    return parser.parse_args()
