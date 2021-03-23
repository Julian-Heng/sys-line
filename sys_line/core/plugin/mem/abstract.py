#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractStoragePlugin
from sys_line.tools.storage import Storage


class AbstractMemory(AbstractStoragePlugin):
    """ Abstract memory class to be implemented by subclass """

    @abstractmethod
    def _used(self):
        pass

    @abstractmethod
    def _total(self):
        pass

    @staticmethod
    def _add_arguments(parser):
        parser.add_argument("-mp", "--mem-prefix", action="store",
                            default=None, choices=Storage.PREFIXES,
                            metavar="prefix", dest="mem.prefix")
        parser.add_argument("-mr", "--mem-round",
                            action="store", type=int, default=None,
                            metavar="int", dest="mem.round")
        parser.add_argument("-mup", "--mem-used-prefix",
                            action="store", default="MiB",
                            choices=Storage.PREFIXES, metavar="prefix",
                            dest="mem.used.prefix")
        parser.add_argument("-mtp", "--mem-total-prefix",
                            action="store", default="MiB",
                            choices=Storage.PREFIXES, metavar="prefix",
                            dest="mem.total.prefix")
        parser.add_argument("-mur", "--mem-used-round",
                            action="store", type=int, default=0,
                            metavar="int", dest="mem.used.round")
        parser.add_argument("-mtr", "--mem-total-round",
                            action="store", type=int, default=0,
                            metavar="int", dest="mem.total.round")
        parser.add_argument("-mpr", "--mem-percent-round",
                            action="store", type=int, default=2,
                            metavar="int", dest="mem.percent.round")
