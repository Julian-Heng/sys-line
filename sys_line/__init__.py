#!/usr/bin/env python3
# pylint: disable=no-member

""" sys-line initialization """

import os
import re

from .options import parse
from .abstract import *
from .systems.darwin import *
from .utils import *
from .string_builder import *


def init_system(options):
    """ Determine what system class this machine should use """
    os_name = os.uname().sysname
    if os_name == "Darwin":
        sys = Darwin(os_name, options)

    return sys


def main():
    """ Main method """
    options = parse()
    system = init_system(options)
    print(string_build(system, options.format))
