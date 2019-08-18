#!/usr/bin/env python3

""" sys-line initialization """

import os
import sys

from importlib import import_module

from .tools.options import parse
from .tools.string_builder import StringBuilder


def init_system(options):
    """ Determine what system class this machine should use """

    os_name = os.uname().sysname
    mod = ".systems.{}".format(os_name.lower())
    try:
        mod = import_module(mod, package=__name__.split(".")[0])
        return getattr(mod, os_name)(os_name, options)
    except (KeyError, ModuleNotFoundError):
        print("Unknown system: {}\nExiting...".format(os_name),
              file=sys.stderr)
        sys.exit(1)


def main():
    """ Main method """
    options = parse()
    system = init_system(options)

    if options.all:
        for k, v in system.return_all():
            print("{}: {}".format(k, v))
    elif options.format:
        print(StringBuilder().build(system, options.format))
    else:
        sys.exit(2)
