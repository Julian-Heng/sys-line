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

# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=too-few-public-methods

""" String builder module to construct a string from a format """

import re

from abc import ABC, abstractmethod


class FormatNode(ABC):
    """ Abstract format node class """

    def __init__(self, system, fmt):
        self.system = system
        self.fmt = fmt

    @abstractmethod
    def build(self):
        """
        Abstract build method to construct the string representation of this
        node
        """


class FormatTree(FormatNode):
    """ A FormatTree class that contains multiple FormatNodes """

    def __init__(self, system, fmt):
        super(FormatTree, self).__init__(system, fmt)
        self.tokens = Tokenizer.tokenize(self.fmt)
        self.nodes = list()

        for i in self.tokens:
            if i.startswith("{") and i != "{}":
                self.nodes.append(FormatInfo(self.system, i))
            else:
                self.nodes.append(FormatString(i))

    def build(self):
        return "".join([i.build() for i in self.nodes])


class FormatInfo(FormatNode):
    """ A FormatInfo class that contains a domain and info to query from """

    FORMAT_OPTIONS = {
        "max_length": int,
    }

    EXTRACT_REGEX = re.compile(
        r"\{\s*(?:(\w+)\s*\.\s*(\w+)\s*(?:\[([^\]]+)\])?)\s*(?:\?)?"
    )

    FORMAT_OPTIONS_EXTRACT_REGEX = re.compile(
        r"({})(?:=(\w+))?".format(r"|".join(FORMAT_OPTIONS.keys()))
    )

    def __init__(self, system, fmt):
        super(FormatInfo, self).__init__(system, fmt)
        self.nodes = list()

        extract = FormatInfo.EXTRACT_REGEX.search(self.fmt)

        self.domain = extract.group(1)
        self.info = extract.group(2)
        self.options = extract.group(3)

        # Set all format options to None
        for k in FormatInfo.FORMAT_OPTIONS:
            setattr(self, k, None)

        if self.fmt.find("?") > -1:
            self.alt_fmt = self.fmt[(self.fmt.find("?") + 1):-1]
            self.alt = FormatTree(self.system, self.alt_fmt)
        else:
            self.alt_fmt = None
            self.alt = None

        # Parse any fomrat specific options within the option string
        self._parse_format_options()

    def _parse_format_options(self):
        if self.options is None:
            return

        opts = dict()

        reg = FormatInfo.FORMAT_OPTIONS_EXTRACT_REGEX
        for fmt_opt in reg.finditer(self.options):
            fmt_opt_key = fmt_opt.group(1)
            fmt_opt_value = fmt_opt.group(2)
            fmt_opt_type = FormatInfo.FORMAT_OPTIONS[fmt_opt_key]

            if fmt_opt_type is int:
                if not fmt_opt_value.isnumeric():
                    msg = f"invalid value for '{fmt_opt_key}': {fmt_opt_value}"
                    raise RuntimeError(msg)
                fmt_opt_value = int(fmt_opt_value)
            elif fmt_opt_type is bool:
                if fmt_opt_value is None:
                    fmt_opt_value = True
                else:
                    fmt_opt_value = bool(fmt_opt_value)
            else:
                fmt_opt_value = None

            opts[fmt_opt_key] = fmt_opt_value

        for k, v in opts.items():
            setattr(self, k, v)

        self.options = reg.sub("", self.options)

    def build(self):
        domain = self.system.query(self.domain)
        info = domain.query(self.info, self.options)
        if info is not None:
            if isinstance(info, bool):
                replace = self.alt.build() if info else ""
            else:
                replace = str(info)
                if self.alt is not None:
                    replace = self.alt.build().replace("{}", replace)
        else:
            replace = ""

        if self.max_length is not None and len(replace) > self.max_length:
            replace = f"{replace[:self.max_length]}..."

        return replace


class FormatString(FormatNode):
    """ A FormatString class that only contains a string """

    def __init__(self, string):
        super(FormatString, self).__init__(None, string)

    def build(self):
        return self.fmt


class Tokenizer():
    """ Tokenizer class to gather tokens in the format string """

    # State enums to store the tokenizer state
    START = -1
    INSIDE = 0
    OUTSIDE = 1

    @staticmethod
    def tokenize(string):
        """
        Find tokens within a string
        Returns a string list
        """

        tokens = list()
        token = ""
        state = Tokenizer.START
        level = 0

        for i in string:
            if i == "{":
                level += 1
                if state == Tokenizer.START:
                    state = Tokenizer.INSIDE
                    if token:
                        tokens.append(token)
                    token = ""
                elif state == Tokenizer.OUTSIDE:
                    state = Tokenizer.INSIDE
                    if token:
                        tokens.append(token)
                    token = ""
                token += i
            elif i == "}":
                level -= 1
                token += i
                if level == 0:
                    state = Tokenizer.OUTSIDE
                    if token:
                        tokens.append(token)
                    token = ""
            else:
                token += i

        if token:
            tokens.append(token)

        return tokens
