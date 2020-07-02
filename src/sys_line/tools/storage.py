#!/usr/bin/env python3

""" Storage module """

from math import log

from .utils import _round


class Storage():
    """ Storage class for storing values with data prefixes """

    # List of supported prefixes
    PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self, value, prefix, rounding=-1):
        if prefix not in Storage.PREFIXES:
            raise TypeError("prefix '{}' not valid".format(prefix))

        self._value = value
        self._prefix = prefix
        self._rounding = rounding

        self._bytes = None

    def __repr__(self):
        if self.rounding > -1:
            value = _round(self.value, self.rounding)
        else:
            value = self.value
        return "{} {}".format(value, self.prefix)

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
            raise TypeError("prefix '{}' not valid".format(prefix))

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
