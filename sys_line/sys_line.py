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

""" sys-line initialization """

import sys

from .systems.abstract import System
from .tools.cli import parse_cli
from .tools.format import FormatTree


def main():
    """ Main method """
    options = parse_cli(sys.argv[1:])
    system = System.create_instance(options)

    if system is not None:
        if options.all is not None:
            domains = options.all if options.all else system.SHORT_DOMAINS
            for domain in domains:
                print(system.query(domain))
        elif options.format:
            for fmt in options.format:
                print(FormatTree(system, fmt).build())
    else:
        sys.exit(2)
