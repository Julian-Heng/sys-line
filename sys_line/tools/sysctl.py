#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

from functools import lru_cache
from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    @property
    @lru_cache(maxsize=1)
    def sysctl(self):
        sysctl = run(["sysctl", "-A", "-e"]).strip().split("\n")
        return dict(i.split("=", 1) for i in sysctl if i and "=" in i)


    def query(self, key: str) -> str:
        """ Fetch a sysctl variable """
        try:
            return self.sysctl[key]
        except KeyError:
            return None
