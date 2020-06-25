#!/usr/bin/env python3

""" Storage module """

from __future__ import annotations


class Storage():
    """ Storage class for storing values with data prefixes """

    PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self, value = 0, prefix = "B", rounding = -1):
        self.value = value
        self.display_value = self.value
        self.__prefix = prefix
        self.rounding = rounding


    def __repr__(self):
        # Prevent cyclic import
        from .utils import _round

        val = self.display_value
        rnd = self.rounding
        prf = self.prefix
        return "{} {}".format(_round(val, rnd) if rnd > -1 else val, prf)


    def __str__(self):
        return self.__repr__()


    def __calc_prefix_delta(self, start, end):
        return self.PREFIXES.index(end) - self.PREFIXES.index(start)


    @property
    def prefix(self):
        """ Returns prefix """
        return self.__prefix


    @prefix.setter
    def prefix(self, prefix):
        """ Sets prefix and changes value """
        if prefix == "auto":
            count = 0
            self.display_value = self.value
            while self.display_value > 1024:
                self.display_value /= 1024
                count += 1
            curr_index = self.PREFIXES.index(self.__prefix) + count
            self.__prefix = self.PREFIXES[curr_index]
        else:
            try:
                delta = self.__calc_prefix_delta(self.__prefix, prefix)
                self.display_value = self.value
                if delta != 0:
                    # Convert the value
                    self.display_value = self.display_value / pow(1024, delta)
                    self.__prefix = prefix
            except ValueError:
                pass


    def set_prefix_without_value(self, prefix):
        """ Change the prefix without the value """
        self.prefix = prefix


    @property
    def bytes(self):
        """ Return storage amount in bytes """
        val = self.value
        delta = self.__calc_prefix_delta(self.prefix, "B")
        return int(val / pow(1024, delta))
