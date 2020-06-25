#!/usr/bin/env python3

""" Storage module """

from __future__ import annotations
import typing


class Storage():
    """ Storage class for storing values with data prefixes """
    PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self,
                 value: int = 0,
                 prefix: str = "B",
                 rounding: int = -1) -> None:
        self.value: int = value
        self.display_value: float = self.value
        self.__prefix: str = prefix
        self.rounding: int = rounding


    def __repr__(self) -> str:
        # Prevent cyclic import
        from .utils import _round

        val = self.display_value
        rnd = self.rounding
        prf = self.prefix
        return "{} {}".format(_round(val, rnd) if rnd > -1 else val, prf)


    def __str__(self) -> str:
        return self.__repr__()


    def __calc_prefix_delta(self, start: str, end: str) -> int:
        return self.PREFIXES.index(end) - self.PREFIXES.index(start)


    @property
    def prefix(self) -> str:
        """ Returns prefix """
        return self.__prefix


    @prefix.setter
    def prefix(self, prefix: str) -> None:
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


    def set_prefix_without_value(self, prefix: str) -> None:
        """ Change the prefix without the value """
        self.prefix = prefix


    @property
    def bytes(self) -> int:
        """ Return storage amount in bytes """
        val = self.value
        delta = self.__calc_prefix_delta(self.prefix, "B")
        return int(val / pow(1024, delta))
