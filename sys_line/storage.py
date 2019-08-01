#!/usr/bin/env python3

""" Storage module """

class Storage():
    """ Storage class for storing values with data prefixes """
    prefixes = ("B", "KiB", "MiB", "GiB")

    def __init__(self, value=0, prefix="B", rounding=-1):
        self.value = value
        self.prefix = prefix
        self.rounding = rounding


    def __repr__(self):
        if self.rounding > -1:
            fmt = "{{:.{}f}} {{}}".format(self.rounding)
        else:
            fmt = "{} {}"

        return fmt.format(self.value, self.prefix)


    def __str__(self):
        return self.__repr__()


    def __add__(self, other):
        return self.value + other


    def __sub__(self, other):
        return self.value - other


    def __mul__(self, other):
        return self.value * other


    def __truediv__(self, other):
        return self.value / other


    def __rtruediv__(self, other):
        return other / self.value


    def __eq__(self, other):
        return self.value == other


    def set_value(self, value):
        """ Change the value """
        self.value = value


    def set_prefix(self, prefix):
        """ Change the current prefix to a another prefix """
        try:
            delta = self.prefixes.index(prefix) - self.prefixes.index(self.prefix)
            if delta != 0:
                # Convert the value
                self.value = self.value / pow(1024, delta)
                self.prefix = prefix
        except ValueError:
            pass


    def set_prefix_without_value(self, prefix):
        """ Change the prefix without the value """
        self.prefix = prefix
