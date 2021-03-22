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

""" Module main """

import logging
import sys

from abc import ABC, abstractmethod

#from sys_line.systems.abstract import System
from sys_line.core.system import System
from sys_line.tools.cli import parse_cli
from sys_line.tools.format import FormatTree
from sys_line.tools.json import json_pretty_string


LOG = logging.getLogger(__name__)


class SysLineApp(ABC):
    """ Abstract SysLine Application """

    def __init__(self, args, options):
        self.args = args
        self.options = options

        if self.options.debug:
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(level=level)
        LOG.debug("command line arguments: %s", self.args)
        LOG.debug("application options: %s", self.options)

        self.system = System.create_instance(options)

    @abstractmethod
    def run(self):
        """ Main application action to be implemented by subclasses """

    @staticmethod
    def create_instance(args):
        """
        Creates a SysLine application depending on the command line arguments
        """
        options = parse_cli(args)
        if options.all is not None:
            fmt = options.output_format

            if fmt == "key_value":
                return SysLineAllKeyValue(args, options)

            if fmt == "json":
                return SysLineAllJson(args, options)

            err_msg = f"unknown output format: '{fmt}'"
            return SysLineError(args, options, err_msg=err_msg, err_code=2)

        if options.format:
            return SysLineFormat(args, options)
        return SysLineError(args, options, err_code=2)


class SysLineAll(SysLineApp):
    """ SysLine application running in 'all' mode """

    def __init__(self, args, options):
        super(SysLineAll, self).__init__(args, options)
        if not self.options.all:
            self.domains = self.system.SHORT_DOMAINS
        else:
            self.domains = options.all

    def run(self):
        self.do_print()
        return 0

    @abstractmethod
    def do_print(self):
        """ Abstract printing method to be implemented by subclasses """


class SysLineAllKeyValue(SysLineAll):
    """
    A subclass of the SysLine application to print all information in key-pair
    format
    """

    def do_print(self):
        for domain in self.domains:
            for name, info in self.system.query(domain).all_info():
                print(f"{domain}.{name}: {info}")


class SysLineAllJson(SysLineAll):
    """
    A subclass of the SysLine application to print all information in json
    format
    """

    def do_print(self):
        print(json_pretty_string(System.to_json(self.system, self.domains)))


class SysLineFormat(SysLineApp):
    """
    A subclass of the SysLine application to print the specified information
    in the user provided format
    """

    def run(self):
        for fmt in self.options.format:
            print(FormatTree(self.system, fmt).build())
        return 0


class SysLineError(SysLineApp):
    """
    A subclass of the SysLine application to return an error code and
    optionally print an error message
    """

    def __init__(self, args, options, err_msg="", err_code=0):
        super(SysLineError, self).__init__(args, options)
        self.err_msg = err_msg
        self.err_code = err_code

    def run(self):
        if self.err_msg:
            LOG.error(self.err_msg)
        return self.err_code


def main():
    """ Main method """
    return SysLineApp.create_instance(sys.argv[1:]).run()


if __name__ == "__main__":
    main()
