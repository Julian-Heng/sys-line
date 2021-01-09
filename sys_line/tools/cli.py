#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" Argument handling """

import argparse
import itertools
import textwrap

from platform import python_build, python_implementation, python_version
from types import SimpleNamespace

from .storage import Storage
from ..systems.abstract import System


def parse_cli(args):
    """ Parse the program arguments """
    domains = ", ".join(System.SHORT_DOMAINS)
    prefixes = ", ".join(Storage.PREFIXES)

    fmt = argparse.RawDescriptionHelpFormatter
    desc = "a simple status line generator"
    epilog = textwrap.dedent(f"""
        list of domains:
            {domains}

        list of prefixes:
            {prefixes}
    """)

    py_impl = python_implementation()
    py_ver = python_version()
    py_build = " ".join(python_build())

    usage_msg = "%(prog)s [options] format..."
    ver = f"%(prog)s ({py_impl} {py_ver}, {py_build})"

    parser = argparse.ArgumentParser(description=desc, epilog=epilog,
                                     usage=usage_msg,
                                     formatter_class=fmt)

    parser.add_argument("format", nargs="*", action="store", type=str,
                        default=[])
    parser.add_argument("-v", "--version", action="version", version=ver)
    parser.add_argument("-a", "--all", nargs="*", choices=System.SHORT_DOMAINS,
                        default=None, metavar="domain")
    parser.add_argument("--debug", action="store_true", default=False)

    groups = {i: parser.add_argument_group(i) for i in System.DOMAINS}

    groups["cpu"].add_argument("-cls", "--cpu-load-short",
                               action="store_true", default=False,
                               dest="cpu.load_avg.short")
    groups["cpu"].add_argument("-cur", "--cpu-usage-round",
                               action="store", type=int, default=2,
                               metavar="int", dest="cpu.cpu_usage.round")
    groups["cpu"].add_argument("-ctr", "--cpu-temp-round",
                               action="store", type=int, default=1,
                               metavar="int", dest="cpu.temp.round")

    groups["memory"].add_argument("-mup", "--mem-used-prefix",
                                  action="store", default="MiB",
                                  choices=Storage.PREFIXES, metavar="prefix",
                                  dest="mem.used.prefix")
    groups["memory"].add_argument("-mtp", "--mem-total-prefix",
                                  action="store", default="MiB",
                                  choices=Storage.PREFIXES, metavar="prefix",
                                  dest="mem.total.prefix")
    groups["memory"].add_argument("-mur", "--mem-used-round",
                                  action="store", type=int, default=0,
                                  metavar="int", dest="mem.used.round")
    groups["memory"].add_argument("-mtr", "--mem-total-round",
                                  action="store", type=int, default=0,
                                  metavar="int", dest="mem.total.round")
    groups["memory"].add_argument("-mpr", "--mem-percent-round",
                                  action="store", type=int, default=2,
                                  metavar="int", dest="mem.percent.round")

    groups["swap"].add_argument("-sup", "--swap-used-prefix",
                                action="store", default="MiB",
                                choices=Storage.PREFIXES, metavar="prefix",
                                dest="swap.used.prefix")
    groups["swap"].add_argument("-stp", "--swap-total-prefix",
                                action="store", default="MiB",
                                choices=Storage.PREFIXES, metavar="prefix",
                                dest="swap.total.prefix")
    groups["swap"].add_argument("-sur", "--swap-used-round",
                                action="store", type=int, default=0,
                                metavar="int", dest="swap.used.round")
    groups["swap"].add_argument("-str", "--swap-total-round",
                                action="store", type=int, default=0,
                                metavar="int", dest="swap.total.round")
    groups["swap"].add_argument("-spr", "--swap-percent-round",
                                action="store", type=int, default=2,
                                metavar="int", dest="swap.percent.round")

    groups["disk"].add_argument("-dd", "--disk", nargs="+", action="append",
                                default=[], metavar="disk",
                                dest="disk.query")
    groups["disk"].add_argument("-dm", "--mount", nargs="+", action="append",
                                default=[], metavar="mount",
                                dest="disk.query")
    groups["disk"].add_argument("-dds", "--disk-dev-short",
                                action="store_true", default=False,
                                dest="disk.dev.short")
    groups["disk"].add_argument("-dup", "--disk-used-prefix",
                                action="store", default="GiB",
                                choices=Storage.PREFIXES, metavar="prefix",
                                dest="disk.used.prefix")
    groups["disk"].add_argument("-dtp", "--disk-total-prefix",
                                action="store", default="GiB",
                                choices=Storage.PREFIXES, metavar="prefix",
                                dest="disk.total.prefix")
    groups["disk"].add_argument("-dur", "--disk-used-round",
                                action="store", type=int, default=2,
                                metavar="int", dest="disk.used.round")
    groups["disk"].add_argument("-dtr", "--disk-total-round",
                                action="store", type=int, default=2,
                                metavar="int", dest="disk.total.round")
    groups["disk"].add_argument("-dpr", "--disk-percent-round",
                                action="store", type=int, default=2,
                                metavar="int", dest="disk.percent.round")

    groups["battery"].add_argument("-bpr", "--bat-percent-round",
                                   action="store", type=int, default=2,
                                   metavar="int", dest="bat.percent.round")
    groups["battery"].add_argument("-bppr", "--bat-power-round",
                                   action="store", type=int, default=2,
                                   metavar="int", dest="bat.power.round")

    groups["network"].add_argument("-ndp", "--net-download-prefix",
                                   action="store", default="KiB",
                                   choices=Storage.PREFIXES, metavar="prefix",
                                   dest="net.download.prefix")
    groups["network"].add_argument("-nup", "--net-upload-prefix",
                                   action="store", default="KiB",
                                   choices=Storage.PREFIXES, metavar="prefix",
                                   dest="net.upload.prefix")
    groups["network"].add_argument("-ndr", "--net-download-round",
                                   action="store", type=int, default=2,
                                   metavar="int", dest="net.download.round")
    groups["network"].add_argument("-nur", "--net-upload-round",
                                   action="store", type=int, default=2,
                                   metavar="int", dest="net.upload.round")

    groups["date"].add_argument("-tdf", "--date-format",
                                action="store", type=str, default="%a, %d %h",
                                metavar="str", dest="date.date.format")
    groups["date"].add_argument("-tf", "--time-format",
                                action="store", type=str, default="%H:%M",
                                metavar="str", dest="date.time.format")

    groups["misc"].add_argument("-mvr", "--misc-volume-round",
                                action="store", type=int, default=0,
                                metavar="int", dest="misc.vol.round")
    groups["misc"].add_argument("-msr", "--misc-screen-round",
                                action="store", type=int, default=0,
                                metavar="int", dest="misc.scr.round")

    return process_args(parser.parse_args(args))


def flatten(_list):
    """ Converts a list of lists into a single list """
    return list(itertools.chain(*_list))


def unique(_list):
    """ Removes duplicate values in a list """
    return list(dict.fromkeys(_list))


def process_args(args):
    """
    Processes the destination of the namespace from the parsed arguments to be
    nested
    """
    options = SimpleNamespace()
    for dest, value in vars(args).items():
        *split, attr = dest.split(".")
        target = options
        for groupspace in split:
            if not hasattr(target, groupspace):
                setattr(target, groupspace, SimpleNamespace())
            target = getattr(target, groupspace)
        setattr(target, attr, value)

    options.disk.query = tuple(unique(flatten(options.disk.query)))

    return options
