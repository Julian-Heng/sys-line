#!/usr/bin/env python3
# pylint: disable=undefined-variable

""" Argument handling """

import argparse
import itertools
import platform
import textwrap

from .storage import Storage
from ..systems.abstract import System


def parse() -> argparse.Namespace:
    """ Parse the program arguments """
    fmt = argparse.RawDescriptionHelpFormatter
    desc = "a simple status line generator"
    epilog = textwrap.dedent("""
        list of domains:
            {}

        list of prefixes:
            {}
    """.format(", ".join(System.SHORT_DOMAINS), ", ".join(Storage.PREFIXES)))

    usage_msg = "%(prog)s [options] format..."
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
                                     usage=usage_msg,
                                     formatter_class=fmt)

    parser.add_argument("format", nargs="?", type=str, default="")
    parser.add_argument("-v", "--version", action="version", version=ver)
    parser.add_argument("-a", "--all", nargs="*", choices=System.SHORT_DOMAINS,
                        default=None, metavar="domain")

    groups = {i: parser.add_argument_group(i) for i in System.DOMAINS}

    groups["cpu"].add_argument("-cls", "--cpu-load-short",
                               action="store_true", default=False)
    groups["cpu"].add_argument("-cur", "--cpu-usage-round",
                               action="store", type=int, default=2,
                               metavar="int")
    groups["cpu"].add_argument("-ctr", "--cpu-temp-round",
                               action="store", type=int, default=1,
                               metavar="int")


    groups["memory"].add_argument("-mup", "--mem-used-prefix",
                                  action="store", default="MiB",
                                  choices=Storage.PREFIXES, metavar="prefix")
    groups["memory"].add_argument("-mtp", "--mem-total-prefix",
                                  action="store", default="MiB",
                                  choices=Storage.PREFIXES, metavar="prefix")
    groups["memory"].add_argument("-mur", "--mem-used-round",
                                  action="store", type=int, default=0,
                                  metavar="int")
    groups["memory"].add_argument("-mtr", "--mem-total-round",
                                  action="store", type=int, default=0,
                                  metavar="int")
    groups["memory"].add_argument("-mpr", "--mem-percent-round",
                                  action="store", type=int, default=2,
                                  metavar="int")


    groups["swap"].add_argument("-sup", "--swap-used-prefix",
                                action="store", default="MiB",
                                choices=Storage.PREFIXES, metavar="prefix")
    groups["swap"].add_argument("-stp", "--swap-total-prefix",
                                action="store", default="MiB",
                                choices=Storage.PREFIXES, metavar="prefix")
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
    mut_group.add_argument("-dd", "--disk", nargs="*", action="append",
                           default=None, metavar="disk")
    mut_group.add_argument("-dm", "--mount", nargs="*", action="append",
                           default=["/"], metavar="mount")


    groups["disk"].add_argument("-dsd", "--disk-short-dev",
                                action="store_true", default=False)
    groups["disk"].add_argument("-dup", "--disk-used-prefix",
                                action="store", default="GiB",
                                choices=Storage.PREFIXES, metavar="prefix")
    groups["disk"].add_argument("-dtp", "--disk-total-prefix",
                                action="store", default="GiB",
                                choices=Storage.PREFIXES, metavar="prefix")
    groups["disk"].add_argument("-dur", "--disk-used-round",
                                action="store", type=int, default=2,
                                metavar="int")
    groups["disk"].add_argument("-dtr", "--disk-total-round",
                                action="store", type=int, default=2,
                                metavar="int")
    groups["disk"].add_argument("-dpr", "--disk-percent-round",
                                action="store", type=int, default=2,
                                metavar="int")


    groups["battery"].add_argument("-bpr", "--bat-percent-round",
                                   action="store", type=int, default=2,
                                   metavar="int")
    groups["battery"].add_argument("-bppr", "--bat-power-round",
                                   action="store", type=int, default=2,
                                   metavar="int")


    groups["network"].add_argument("-ndp", "--net-download-prefix",
                                   action="store", default="KiB",
                                   choices=Storage.PREFIXES, metavar="prefix")
    groups["network"].add_argument("-nup", "--net-upload-prefix",
                                   action="store", default="KiB",
                                   choices=Storage.PREFIXES, metavar="prefix")
    groups["network"].add_argument("-ndr", "--net-download-round",
                                   action="store", type=int, default=2,
                                   metavar="int")
    groups["network"].add_argument("-nur", "--net-upload-round",
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

    result = parser.parse_args()

    flatten = lambda l: list(itertools.chain(*l))
    unique = lambda l: list(dict.fromkeys(l))
    if result.disk is not None:
        result.disk = unique(flatten(result.disk))
    if len(result.mount) > 1:
        result.mount = unique(flatten(result.mount[1:]))

    return result
