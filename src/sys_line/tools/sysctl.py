#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    def __init__(self):
        self.sysctl = dict()
        sysctl = run(["sysctl", "-A", "-e"]).strip().split("\n")
        self.sysctl = dict(i.split("=", 1) for i in sysctl if i and "=" in i)

    def query(self, key):
        """ Fetch a sysctl variable """
        try:
            return self.sysctl[key]
        except KeyError:
            return None
