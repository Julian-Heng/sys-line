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

import logging
import sys

from .systems.abstract import System
from .tools.cli import parse_cli
from .tools.format import FormatTree
from .tools.json import json_pretty_string


LOG = logging.getLogger(__name__)


def main():
    """ Main method """
    args = sys.argv[1:]
    options = parse_cli(args)

    if options.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level)
    LOG.debug("command line arguments: %s", args)
    LOG.debug("application options: %s", options)

    system = System.create_instance(options)

    if system is not None:
        if options.all is not None:
            if not options.all:
                domains = system.SHORT_DOMAINS
            else:
                domains = options.all
            sys_line_print_all(system, domains, options.output_format)
        elif options.format:
            for fmt in options.format:
                print(FormatTree(system, fmt).build())
    else:
        sys.exit(2)


def sys_line_print_all(system, domains, fmt):
    """ Prints all info in domains within a system """
    if fmt == "key_value":
        for domain in domains:
            for name, info in system.query(domain).all_info():
                print(f"{domain}.{name}: {info}")
    elif fmt == "json":
        print(json_pretty_string(System.to_json(system, domains)))
    else:
        LOG.error("unknown output format: '%s'", fmt)
        sys.exit(2)
