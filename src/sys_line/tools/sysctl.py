#!/usr/bin/env python3
# pylint: disable=too-few-public-methods

""" Sysctl module """

from functools import lru_cache

from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    @staticmethod
    @lru_cache()
    def query(key):
        """ Fetch a sysctl variable """
        return run(["sysctl", "-n", key]).strip()
