#!/usr/bin/env python3

""" Storage module """


class Storage():
    """ Storage class for storing values with data prefixes """
    PREFIXES = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self,
                 value: int = 0,
                 prefix: str = "B",
                 rounding: int = -1) -> None:
        self.__value = value
        self.__prefix = prefix
        self.__rounding = rounding


    def __repr__(self) -> str:
        # Prevent cyclic import
        from .utils import _round

        val = self.value
        rnd = self.rounding
        prf = self.prefix
        return "{} {}".format(_round(val, rnd) if rnd > -1 else val, prf)


    def __str__(self) -> str:
        return self.__repr__()


    def __add__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.value = val + other

        if is_storage:
            tmp_prefix = self.prefix
            self.set_prefix_without_value("B")
            self.prefix = tmp_prefix

        return self


    def __sub__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.value = val - other

        if is_storage:
            tmp_prefix = self.prefix
            self.set_prefix_without_value("B")
            self.prefix = tmp_prefix

        return self


    def __mul__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.value = val * other

        if is_storage:
            tmp_prefix = self.prefix
            self.set_prefix_without_value("B")
            self.prefix = tmp_prefix

        return self


    def __truediv__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.value = val / other

        if is_storage:
            tmp_prefix = self.prefix
            self.set_prefix_without_value("B")
            self.prefix = tmp_prefix

        return self


    def __rtruediv__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.value = other / val

        if is_storage:
            tmp_prefix = self.prefix
            self.set_prefix_without_value("B")
            self.prefix = tmp_prefix

        return self


    def __eq__(self, other: object) -> bool:
        return self.value == other


    def __bool__(self) -> bool:
        return bool(self.value)


    def __calc_prefix_delta(self, start: int, end: int) -> int:
        return self.PREFIXES.index(end) - self.PREFIXES.index(start)


    def __check_storage(self, other: object) -> (int, int, bool):
        chk = isinstance(other, Storage)
        return (self.bytes if chk else self.value,
                other.bytes if chk else other, chk)


    @property
    def value(self) -> [int, float]:
        return self.__value


    @value.setter
    def value(self, value: int) -> None:
        self.__value = value


    @property
    def prefix(self) -> str:
        return self.__prefix


    @prefix.setter
    def prefix(self, prefix: str) -> None:
        if prefix == "auto":
            count = 0
            while self.__value > 1024:
                self.__value /= 1024
                count += 1
            curr_index = self.PREFIXES.index(self.__prefix) + count
            self.__prefix = self.PREFIXES[curr_index]
        else:
            try:
                delta = self.__calc_prefix_delta(self.__prefix, prefix)
                if delta != 0:
                    # Convert the value
                    self.__value = self.__value / pow(1024, delta)
                    self.__prefix = prefix
            except ValueError:
                pass


    @property
    def rounding(self) -> int:
        return self.__rounding


    @rounding.setter
    def rounding(self, rounding) -> None:
        self.__rounding = rounding


    def set_prefix_without_value(self, prefix: str) -> None:
        """ Change the prefix without the value """
        self.prefix = prefix


    @property
    def bytes(self) -> int:
        """ Return storage amount in bytes """
        val = self.value
        delta = self.__calc_prefix_delta(self.prefix, "B")
        return int(val / pow(1024, delta))
