#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" String builder module to construct a string from a format """

import re
import typing

from ..systems.abstract import System


class StringBuilder():
    """ String Builder class """

    def __init__(self) -> None:
        self.extract_reg = re.compile(r"\{((\w+)\.(\w+))(?:\?)?")
        self.trim_reg_1 = re.compile(r"\{\}")
        self.trim_reg_2 = re.compile(r"\{\?|\}$")


    def build(self, sys: System, fmt: str) -> str:
        """ Recursive function to build a string from a format """
        out = ""

        for i in tokenize(fmt):
            extract = self.extract_reg.search(i)
            if extract is not None:
                domain = extract.group(2)
                info = extract.group(3)
                replace = getattr(getattr(sys, domain), info)

                parse = re.sub(extract.group(1), "", i)

                if replace is not None:
                    if isinstance(replace, bool):
                        if replace:
                            replace = self.build(sys, parse)
                        else:
                            replace = ""
                    else:
                        replace = str(replace)
                        replace = self.trim_reg_1.sub(replace, parse, 1)
                        replace = self.trim_reg_2.sub("", replace)
                        if self.extract_reg.search(i):
                            replace = self.build(sys, replace)
                    out += replace
            else:
                out += i

        return out


def tokenize(string: str) -> typing.List[str]:
    """
    Find tokens within a string
    Returns a string list
    """
    tokens = list()
    curr = ""
    state = ""
    level = 0

    for i in string:
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
