#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractPlugin
from sys_line.tools.utils import round_trim


class AbstractMisc(AbstractPlugin):
    """ Misc class for fetching miscellaneous information """

    @abstractmethod
    def _vol(self):
        """ Abstract volume method to be implemented by subclass """

    def vol(self, options=None):
        """ Volume method """
        if options is None:
            options = self.default_options

        vol = self._vol()
        if vol is None:
            return None

        vol = round_trim(vol, options.vol.round)
        return vol

    @abstractmethod
    def _scr(self):
        """ Abstract screen brightness method to be implemented by subclass """

    def scr(self, options=None):
        """ Screen brightness method """
        if options is None:
            options = self.default_options

        current_scr, max_scr = self._scr()
        if current_scr is None or max_scr is None:
            return None

        scr = percent(current_scr, max_scr)
        scr = round_trim(scr, options.scr.round)
        return scr

    @staticmethod
    def _add_arguments(parser):
        parser.add_argument("-mvr", "--misc-volume-round", action="store",
                            type=int, default=0, metavar="int",
                            dest="misc.vol.round")
        parser.add_argument("-msr", "--misc-screen-round", action="store",
                            type=int, default=0, metavar="int",
                            dest="misc.scr.round")
