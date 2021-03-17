#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2021  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" Storage module """

from math import log

from .utils import round_trim


class Storage():
    """ Storage class for storing values with data prefixes """

    # List of supported prefixes
    PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self, value, prefix, rounding=-1):
        if prefix not in Storage.PREFIXES:
            raise TypeError(f"prefix '{prefix}' not valid")

        self._value = value
        self._prefix = prefix
        self._rounding = rounding

        self._bytes = None

    def __repr__(self):
        if self.rounding > -1:
            value = round_trim(self.value, self.rounding)
        else:
            value = self.value
        return f"{value} {self.prefix}"

    def __str__(self):
        return self.__repr__()

    @property
    def value(self):
        """ Returns the value under the current prefix """
        return self._value

    @property
    def prefix(self):
        """ Returns the prefix """
        return self._prefix

    @prefix.setter
    def prefix(self, prefix):
        """ Sets the prefix and convert the value accordingly """
        if prefix not in Storage.PREFIXES:
            raise TypeError(f"prefix '{prefix}' not valid")

        if prefix == "auto":
            if self.bytes != 0:
                index = int(log(self.bytes, 1024))
                self._value = self.bytes / pow(1024, index)
                self._prefix = Storage.PREFIXES[index]
        else:
            distance = Storage._distance_between("B", prefix)
            if distance > 0:
                self._value = self.bytes / pow(1024, distance)
            self._prefix = prefix

    @property
    def rounding(self):
        """ Returns the number of places to be rounded to """
        return self._rounding

    @property
    def bytes(self):
        """ Returns the value in bytes """
        if self._bytes is None:
            distance = Storage._distance_between("B", self.prefix)
            if distance > 0:
                self._bytes = self.value * pow(1024, distance)
            else:
                self._bytes = self.value
        return self._bytes

    @staticmethod
    def _distance_between(i, j):
        return Storage.PREFIXES.index(j) - Storage.PREFIXES.index(i)
