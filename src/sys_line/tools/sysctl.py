#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    def __init__(self):
        self._sysctl = None

    @property
    def sysctl(self):
        if self._sysctl is None:
            sysctl = run(["sysctl", "-A", "-e"]).strip().split("\n")
            self._sysctl = dict(i.split("=", 1)
                                for i in sysctl if i and "=" in i)

        return self._sysctl

    def query(self, key):
        """ Fetch a sysctl variable """
        if key in self.sysctl:
            return self.sysctl[key]
        else:
            return None
