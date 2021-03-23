#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractStoragePlugin
from sys_line.tools.storage import Storage


class AbstractSwap(AbstractStoragePlugin):
    """ Abstract swap class to be implemented by subclass """

    @abstractmethod
    def _used(self):
        pass

    @abstractmethod
    def _total(self):
        pass

    @staticmethod
    def _add_arguments(parser):
        parser.add_argument("-sp", "--swap-prefix", action="store",
                            default=None, choices=Storage.PREFIXES,
                            metavar="prefix", dest="swap.prefix")
        parser.add_argument("-sr", "--swap-round", action="store", type=int,
                            default=None, metavar="int", dest="swap.round")
        parser.add_argument("-sup", "--swap-used-prefix", action="store",
                            default="MiB", choices=Storage.PREFIXES,
                            metavar="prefix", dest="swap.used.prefix")
        parser.add_argument("-stp", "--swap-total-prefix", action="store",
                            default="MiB", choices=Storage.PREFIXES,
                            metavar="prefix", dest="swap.total.prefix")
        parser.add_argument("-sur", "--swap-used-round", action="store",
                            type=int, default=0, metavar="int",
                            dest="swap.used.round")
        parser.add_argument("-str", "--swap-total-round", action="store",
                            type=int, default=0, metavar="int",
                            dest="swap.total.round")
        parser.add_argument("-spr", "--swap-percent-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="swap.percent.round")
