#!/usr/bin/env python3

""" sys-line initialization """

import sys
import os

from .tools.options import parse
from .tools.string_builder import StringBuilder

from .systems.darwin import Darwin
from .systems.linux import Linux
from .systems.freebsd import FreeBSD


def init_system(options):
    """ Determine what system class this machine should use """
    systems = {
        "Darwin": Darwin,
        "Linux": Linux,
        "FreeBSD": FreeBSD
    }

    os_name = os.uname().sysname
    try:
        return systems[os_name](os_name, options)
    except KeyError:
        print("Unknown system: {}\nExiting...".format(os_name),
              file=sys.stderr)
        sys.exit(1)


def main():
    """ Main method """
    options = parse()
    system = init_system(options)
    print(StringBuilder().build(system, options.format))
