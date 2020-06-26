#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" String builder module to construct a string from a format """

import re

from abc import ABC, abstractmethod

from ..systems.abstract import System


class FormatNode(ABC):

    @abstractmethod
    def build(self):
        pass


class FormatTree(FormatNode):

    def __init__(self, system, fmt):
        super(FormatTree, self).__init__()
        self.system = system
        self.fmt = fmt
        self.nodes = list()

    def build(self):
        for i in self._tokenize():
            if i.startswith("{"):
                self.nodes.append(FormatInfo(self.system, i))
            else:
                self.nodes.append(FormatString(i))

        return "".join([i.build() for i in self.nodes])

    def _tokenize(self):
        """
        Find tokens within a string
        Returns a string list
        """
        tokens = list()
        curr = ""
        state = ""
        level = 0

        for i in self.fmt:
            if i == "{":
                level += 1
                if state == "":
                    state = "in"
                    if curr != "":
                        tokens.append(curr)
                    curr = ""
                elif state == "out":
                    state = "in"
                    if curr != "":
                        tokens.append(curr)
                    curr = ""
                curr += i
            elif i == "}":
                level -= 1
                curr += i
                if level == 0:
                    state = "out"
                    if curr != "":
                        tokens.append(curr)
                    curr = ""
            else:
                curr += i

        tokens.append(curr)

        return tokens


class FormatInfo(FormatNode):

    EXTRACT_REGEX = re.compile(r"\{((\w+)\.(\w+))(?:\?)?")

    def __init__(self, system, fmt):
        super(FormatInfo, self).__init__()

        self.system = system
        self.fmt = fmt
        self.nodes = list()

        extract = self.EXTRACT_REGEX.search(self.fmt)
        self.domain = extract.group(2)
        self.info = extract.group(3)

        if self.fmt.find("?") > -1:
            alt = self.fmt[(self.fmt.find("?") + 1):-1]
            alt = alt.replace("{}", "{{{}.{}}}".format(self.domain, self.info))
            self.alt = FormatTree(self.system, alt)
        else:
            self.alt = None

    def build(self):
        replace = getattr(self.system, self.domain).query(self.info, None)
        if replace is not None:
            if isinstance(replace, bool):
                replace = self.alt.build() if replace else ""
            else:
                replace = str(replace)
                if self.alt is not None:
                    replace = self.alt.build()
        else:
            replace = ""

        return replace


class FormatString(FormatNode):

    def __init__(self, string):
        super(FormatString, self).__init__()
        self.string = string

    def build(self):
        return self.string
