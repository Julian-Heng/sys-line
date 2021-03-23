#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractPlugin
from sys_line.tools.utils import unix_epoch_to_str


class AbstractBattery(AbstractPlugin):
    """ Abstract battery class to be implemented by subclass """

    @staticmethod
    def _post_import_hook(plugin):
        pass

    @abstractmethod
    def is_present(self, options=None):
        """ Abstract battery present method to be implemented by subclass """

    @abstractmethod
    def is_charging(self, options=None):
        """ Abstract battery charging method to be implemented by subclass """

    @abstractmethod
    def is_full(self, options=None):
        """ Abstract battery full method to be implemented by subclass """

    @abstractmethod
    def _percent(self):
        """ Abstract battery percent method to be implemented by subclass """

    def percent(self, options=None):
        """ Battery percent method """
        if options is None:
            options = self.default_options

        if not self.is_present(options):
            return None

        current, full = self._percent()
        if current is None or full is None:
            return None

        perc = percent(current, full)
        perc = round_trim(perc, options.percent.round)
        return perc

    @abstractmethod
    def _time(self):
        """
        Abstract battery time remaining method to be implemented by subclass
        """

    def time(self, options=None):
        """ Battery time method """
        return unix_epoch_to_str(self._time())

    @abstractmethod
    def _power(self):
        """
        Abstract battery power usage method to be implemented by subclass
        """

    def power(self, options=None):
        """
        Power usage method
        """
        if options is None:
            options = self.default_options

        if not self.is_present(options):
            return None

        power = self._power()
        if power is None:
            return None

        power = round_trim(power, options.power.round)
        return power

    @staticmethod
    def _add_arguments(parser):
        parser.add_argument("-bpr", "--bat-percent-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="bat.percent.round")
        parser.add_argument("-bppr", "--bat-power-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="bat.power.round")


class BatteryStub(AbstractBattery):
    """ Sub-Battery class for systems that has no battery """

    def is_present(self, options=None):
        return False

    def is_charging(self, options=None):
        return None

    def is_full(self, options=None):
        return None

    def _percent(self):
        return None, None

    def _time(self):
        return 0

    def _power(self):
        return None
