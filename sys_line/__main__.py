#!/usr/bin/env python3
# pylint: disable=no-member

""" sys-line initialization """

import sys
import os
import re

from .options import parse
from .abstract import *
from .utils import *
from .string_builder import StringBuilder

from .systems.darwin import *
from .systems.linux import *
from .systems.freebsd import *


def init_system(options):
    """ Determine what system class this machine should use """
    systems = {
        "Darwin": Darwin,
        "Linux": Linux,
        "FreeBSD": FreeBSD
    }

    os_name = os.uname().sysname
    try:
        system = systems[os_name](os_name, options)
    except KeyError:
        print("Unknown system: {}\nExiting...".format(os_name),
              file=sys.stderr)
        sys.exit(1)

    return system


def main():
    """ Main method """
    options = parse()
    system = init_system(options)
    print(StringBuilder().build(system, options.format))


if __name__ == "__main__":
    main()
