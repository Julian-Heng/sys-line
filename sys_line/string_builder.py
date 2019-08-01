#!/usr/bin/env python3

""" String builder module to construct a string from a format """

import re


def string_build(sys, fmt):
    """ Recursive function to build a string from a format """
    out = ""

    for i in tokenize(fmt):
        extract = re.search(r"\{((\w+)\.(\w+))(?:\?)?", i)
        if extract is not None:
            domain = extract.group(2)
            info = extract.group(3)
            sys.fetch(domain, info)
            replace = sys.get(domain, info)

            parse = re.sub(extract.group(1), "", i)

            if replace is not None:
                if isinstance(replace, bool):
                    if replace:
                        replace = string_build(sys, parse)
                    else:
                        replace = ""
                else:
                    replace = str(replace)
                    replace = re.sub(r"\{\}", replace, parse, 1)
                    replace = re.sub(r"\{\?|\}$", "", replace)
                    if re.search(r"\{((\w+)\.(\w+))(?:\?)?", i):
                        replace = string_build(sys, replace)
                out += replace
        else:
            out += i

    return out


def tokenize(string):
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
