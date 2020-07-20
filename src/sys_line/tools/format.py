#!/usr/bin/env python3
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

    EXTRACT_REGEX = re.compile(r"\{(?:(\w+)\.(\w+)(?:\[([^\]]+)\])?)(?:\?)?")

    def __init__(self, system, fmt):
        super(FormatInfo, self).__init__(system, fmt)
        self.nodes = list()

        extract = FormatInfo.EXTRACT_REGEX.search(self.fmt)

        self.domain = extract.group(1)
        self.info = extract.group(2)
        self.options = extract.group(3)

        if self.fmt.find("?") > -1:
            self.alt_fmt = self.fmt[(self.fmt.find("?") + 1):-1]
            self.alt = FormatTree(self.system, self.alt_fmt)
        else:
            self.alt_fmt = None
            self.alt = None

    def build(self):
        replace = self.system.query(self.domain, self.info, self.options)
        if replace is not None:
            if isinstance(replace, bool):
                replace = self.alt.build() if replace else ""
            else:
                replace = str(replace)
                if self.alt is not None:
                    replace = self.alt.build().replace("{}", replace)
        else:
            replace = ""

        return replace


class FormatString(FormatNode):
    """ A FormatString class that only contains a string """

    def __init__(self, string):
        super(FormatString, self).__init__(None, string)

    def build(self):
        return self.fmt


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
        token = ""
        state = Tokenizer.State.START
        level = 0

        for i in string:
            if i == "{":
                level += 1
                if state == Tokenizer.State.START:
                    state = Tokenizer.State.INSIDE
                    if token:
                        tokens.append(token)
                    token = ""
                elif state == Tokenizer.State.OUTSIDE:
                    state = Tokenizer.State.INSIDE
                    if token:
                        tokens.append(token)
                    token = ""
                token += i
            elif i == "}":
                level -= 1
                token += i
                if level == 0:
                    state = Tokenizer.State.OUTSIDE
                    if token:
                        tokens.append(token)
                    token = ""
            else:
                token += i

        if token:
            tokens.append(token)

        return tokens
