#!/usr/bin/env python3
# pylint: disable=invalid-name

""" sys-line initialization """

import os
import sys

from argparse import Namespace
from importlib import import_module

from .tools.options import parse
from .tools.format import FormatTree
from .systems.abstract import System


def init_system(options):
    """ Determine what system class this machine should use """
    os_name = os.uname().sysname

    # Module system files format is the output of "uname -s" in lowercase
    mod_name = ".systems.{}".format(os_name.lower())
    try:
        mod = import_module(mod_name, package=__name__.split(".")[0])

        # Instantiate system
        system = getattr(mod, os_name)(options)
    except ModuleNotFoundError:
        print("Unknown system: {}\nExiting...".format(os_name),
              file=sys.stderr)
        system = None

    return system


def main():
    """ Main method """
    options = parse()
    system = init_system(options)

    if system is not None:
        if options.all is not None:
            domains = options.all if options.all else system.SHORT_DOMAINS
            for domain in domains:
                print(getattr(system, domain))
        elif options.format:
            print(FormatTree(system, options.format).build())
    else:
        sys.exit(2)
