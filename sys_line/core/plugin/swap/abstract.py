#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractStoragePlugin


class AbstractSwap(AbstractStoragePlugin):
    """ Abstract swap class to be implemented by subclass """

    @abstractmethod
    def _used(self):
        pass

    @abstractmethod
    def _total(self):
        pass
