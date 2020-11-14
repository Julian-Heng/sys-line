#!/usr/bin/env python3
# pylint: disable=undefined-variable

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

    parser.add_argument("format", nargs="*", action="append", type=str,
                        default=[""])
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

    groups["disk"].add_argument("-dd", "--disk", nargs="*", action="append",
                                default=[], metavar="disk", dest="disk_disk")
    groups["disk"].add_argument("-dm", "--mount", nargs="*", action="append",
                                default=["/"], metavar="mount",
                                dest="disk_mount")
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
                                metavar="str", dest="date_date_format")
    groups["date"].add_argument("-tf", "--time-format",
                                action="store", type=str, default="%H:%M",
                                metavar="str", dest="date_time_format")

    groups["misc"].add_argument("-mvr", "--misc-volume-round",
                                action="store", type=int, default=0,
                                metavar="int")
    groups["misc"].add_argument("-msr", "--misc-screen-round",
                                action="store", type=int, default=0,
                                metavar="int")

    return process_args(parser.parse_args(args))


def flatten(_list):
    """ Converts a list of lists into a single list """
    return list(itertools.chain(*_list))


def unique(_list):
    """ Removes duplicate values in a list """
    return list(dict.fromkeys(_list))


def dict_to_namespace(_dict):
    """ Converts a dictionary to a simple namespace recursively """
    ret = SimpleNamespace()
    for attr_name, attr_value in _dict.items():
        if isinstance(attr_value, dict):
            attr_value = dict_to_namespace(attr_value)
        setattr(ret, attr_name, attr_value)
    return ret


def process_args(args):
    """
    Converts the namespace from argparse.parse_args to a simple namespace
    """
    options = dict()

    # Split the argparse namespace into multiple namespaces
    for key, value in vars(args).items():
        if key in ["format", "all"]:
            options[key] = value
        else:
            domain, info = key.split("_", 1)
            if domain not in options:
                options[domain] = dict()
            options[domain][info] = value

    result = dict_to_namespace(options)

    # Flatten the list of formats if it is not the default
    if result.format != [""]:
        result.format = flatten(result.format[1:])

    disk = result.disk.disk
    mount = result.disk.mount

    # Flatten the list of disks if it is not the default
    if disk:
        disk = unique(flatten(disk))
        # Clear mount list if it is default since disk is set
        if mount == ["/"]:
            mount = list()

    # Flatten the list of mounts if it is not default
    if mount and mount != ["/"]:
        mount = unique(flatten(mount[1:]))

    result.disk.disk = disk
    result.disk.mount = mount

    return result
