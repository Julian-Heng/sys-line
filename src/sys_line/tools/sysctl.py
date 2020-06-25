#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

import typing

from functools import lru_cache
from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    def __init__(self):
        self.sysctl: typing.Dict[str, str] = dict()
        sysctl = run(["sysctl", "-A", "-e"]).strip().split("\n")
        self.sysctl = dict(i.split("=", 1) for i in sysctl if i and "=" in i)


    def query(self, key: str) -> typing.Union[str, None]:
        """ Fetch a sysctl variable """
        try:
            return self.sysctl[key]
        except KeyError:
            return None
