#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2021  Julian Heng
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

# pylint: disable=too-many-statements

""" Argument handling """

import argparse
import itertools
import textwrap

from platform import python_build, python_implementation, python_version
from types import SimpleNamespace

from sys_line.tools.storage import Storage


def parse_early_cli(args):
    """ Parse the program arguments excluding plugin flags """
    py_impl = python_implementation()
    py_ver = python_version()
    py_build = " ".join(python_build())
    ver = f"%(prog)s ({py_impl} {py_ver}, {py_build})"

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-v", "--version", action="version", version=ver)
    parser.add_argument("--debug", action="store_true", default=False)
    return parser.parse_known_args(args)


def parse_cli(plugins, args):
    """ Parse the program arguments """
    output_formats_choices = ("key_value", "json")
    output_formats = ", ".join(output_formats_choices)
    domains = ", ".join(plugins.keys())
    prefixes = ", ".join(Storage.PREFIXES)

    fmt = argparse.RawDescriptionHelpFormatter
    desc = "a simple status line generator"
    epilog = textwrap.dedent(f"""
        list of output formats:
            {output_formats}

        list of domains:
            {domains}

        list of prefixes:
            {prefixes}
    """)

    usage_msg = "%(prog)s [options] format..."

    parser = argparse.ArgumentParser(description=desc, epilog=epilog,
                                     usage=usage_msg,
                                     formatter_class=fmt)

    parser.add_argument("format", nargs="*", action="store", type=str,
                        default=[])
    parser.add_argument("-a", "--all", nargs="*", action="store",
                        default=None, metavar="domain")
    parser.add_argument("--output-format", choices=output_formats_choices,
                        default="key_value", metavar="output_format")

    for plugin_name, plugin_class in plugins.items():
        plugin_class._add_arguments(parser.add_argument_group(plugin_name))

    options = convert_parsed_to_options(parser.parse_args(args))
    for plugin_name, plugin_class in plugins.items():
        try:
            plugin_options = getattr(options, plugin_name)
            plugin_options = plugin_class._post_argument_parse_hook(plugin_options)
            setattr(options, plugin_name, plugin_options)
        except AttributeError:
            pass

    return options


def convert_parsed_to_options(args):
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

    return options
