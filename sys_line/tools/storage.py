#!/usr/bin/env python3

""" Storage module """



class Storage():
    """ Storage class for storing values with data prefixes """
    prefixes = ("B", "KiB", "MiB", "GiB", "TiB", "auto")

    def __init__(self,
                 value: int = 0,
                 prefix: str = "B",
                 rounding: int = -1) -> None:
        self.value = value
        self.prefix = prefix
        self.rounding = rounding


    def __repr__(self) -> str:
        from .utils import _round

        val = self.value
        rnd = self.rounding
        prf = self.prefix
        return "{} {}".format(_round(val, rnd) if rnd > -1 else val, prf)


    def __str__(self) -> str:
        return self.__repr__()


    def __add__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.set_value(val + other)

        if is_storage:
            tmp_prefix = self.get_prefix()
            self.set_prefix_without_value("B")
            self.set_prefix(tmp_prefix)

        return self

    def __sub__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.set_value(val - other)

        if is_storage:
            tmp_prefix = self.get_prefix()
            self.set_prefix_without_value("B")
            self.set_prefix(tmp_prefix)

        return self


    def __mul__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.set_value(val * other)

        if is_storage:
            tmp_prefix = self.get_prefix()
            self.set_prefix_without_value("B")
            self.set_prefix(tmp_prefix)

        return self


    def __truediv__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.set_value(val / other)

        if is_storage:
            tmp_prefix = self.get_prefix()
            self.set_prefix_without_value("B")
            self.set_prefix(tmp_prefix)

        return self


    def __rtruediv__(self, other: object) -> None:
        val, other, is_storage = self.__check_storage(other)
        self.set_value(other / val)

        if is_storage:
            tmp_prefix = self.get_prefix()
            self.set_prefix_without_value("B")
            self.set_prefix(tmp_prefix)

        return self


    def __eq__(self, other: object) -> bool:
        return self.value == other


    def __bool__(self) -> bool:
        return bool(self.value)


    def __calc_prefix_delta(self, start: int, end: int) -> int:
        return self.prefixes.index(end) - self.prefixes.index(start)


    def __check_storage(self, other: object) -> (int, int, bool):
        val = self.get_bytes() if isinstance(other, Storage) else self.value
        oth = other.get_bytes() if isinstance(other, Storage) else other
        return val, oth, isinstance(other, Storage)


    def set_value(self, value: int) -> None:
        """ Change the value """
        self.value = value


    def set_prefix(self, prefix: str) -> None:
        """ Change the current prefix to a another prefix """
        if prefix == "auto":
            count = 0
            while self.value > 1024:
                self.value /= 1024
                count += 1
            curr_index = self.prefixes.index(self.prefix) + count
            self.prefix = self.prefixes[curr_index]
        else:
            try:
                delta = self.__calc_prefix_delta(self.prefix, prefix)
                if delta != 0:
                    # Convert the value
                    self.value = self.value / pow(1024, delta)
                    self.prefix = prefix
            except ValueError:
                pass


    def get_value(self) -> int:
        """ Return value """
        return self.value


    def get_prefix(self) -> str:
        """ Return prefix """
        return self.value


    def set_prefix_without_value(self, prefix: str) -> None:
        """ Change the prefix without the value """
        self.prefix = prefix


    def get_bytes(self) -> int:
        """ Return storage amount in bytes """
        val = self.value
        delta = self.__calc_prefix_delta(self.prefix, "B")
        return int(val / pow(1024, delta))
