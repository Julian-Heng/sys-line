#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" String builder module to construct a string from a format """

import re

from abc import ABC, abstractmethod


class FormatNode(ABC):
    """ Abstract format node class """

    @abstractmethod
    def build(self):
        """
        Abstract build method to construct the string repensentation of
        this node
        """


class FormatTree(FormatNode):
    """ A FormatTree class that contains multiple FormatNodes """

    def __init__(self, system, fmt):
        super(FormatTree, self).__init__()
        self.system = system
        self.fmt = fmt
        self.nodes = list()

    def build(self):
        for i in Tokenizer.tokenize(self.fmt):
            if i.startswith("{"):
                self.nodes.append(FormatInfo(self.system, i))
            else:
                self.nodes.append(FormatString(i))

        return "".join([i.build() for i in self.nodes])


class FormatInfo(FormatNode):
    """ A FormatInfo class that contains a domain and info to query from """

    EXTRACT_REGEX = re.compile(r"\{(?:(\w+)(?:\[([^\]]+)\])?\.(\w+))(?:\?)?")

    def __init__(self, system, fmt):
        super(FormatInfo, self).__init__()

        self.system = system
        self.fmt = fmt
        self.nodes = list()

        extract = self.EXTRACT_REGEX.search(self.fmt)
        self.domain = extract.group(1)
        self.options = extract.group(2)
        self.info = extract.group(3)

        if self.fmt.find("?") > -1:
            alt = self.fmt[(self.fmt.find("?") + 1):-1]
            self.alt = [FormatTree(self.system, i)
                        for i in Tokenizer.tokenize(alt)]
        else:
            self.alt = None

    def build(self):
        replace = getattr(self.system, self.domain).query(self.info,
                                                          self.options)
        if replace is not None:
            if isinstance(replace, bool):
                replace = self._build_alt(replace) if replace else ""
            else:
                replace = str(replace)
                if self.alt is not None:
                    replace = self._build_alt(replace)
        else:
            replace = ""

        return replace

    def _build_alt(self, replace):
        nodes = [replace if i.fmt == "{}" else i.build() for i in self.alt]
        return "".join(nodes)


class FormatString(FormatNode):
    """ A FormatString class that only contains a string """

    def __init__(self, string):
        super(FormatString, self).__init__()
        self.string = string

    def build(self):
        return self.string


class Tokenizer():
    """ Tokenizer class to gather tokens in the format string """

    class State:
        """ State class to store the tokenizer state """
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
        curr = ""
        state = Tokenizer.State.START
        level = 0

        for i in string:
            if i == "{":
                level += 1
                if state == Tokenizer.State.START:
                    state = Tokenizer.State.INSIDE
                    if curr:
                        tokens.append(curr)
                    curr = ""
                elif state == Tokenizer.State.OUTSIDE:
                    state = Tokenizer.State.INSIDE
                    if curr:
                        tokens.append(curr)
                    curr = ""
                curr += i
            elif i == "}":
                level -= 1
                curr += i
                if level == 0:
                    state = Tokenizer.State.OUTSIDE
                    if curr:
                        tokens.append(curr)
                    curr = ""
            else:
                curr += i

        tokens.append(curr)

        return tokens
