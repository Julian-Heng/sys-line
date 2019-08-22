#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    def __init__(self):
        check = lambda i: i and ":" in i
        self.sysctl = run(["sysctl", "-A"]).strip().split("\n")
        self.sysctl = dict(i.split(":", 1) for i in self.sysctl if check(i))


    def query(self, key: str) -> str:
        """ Fetch a sysctl variable """
        try:
            return self.sysctl[key]
        except KeyError:
            return None
