#!/usr/bin/env python3

from abc import abstractmethod
from pathlib import Path
from logging import getLogger
from functools import lru_cache

from sys_line.core.plugin.bat.abstract import AbstractBattery, BatteryStub


LOG = getLogger(__name__)


class Battery(AbstractBattery):
    """ A Linux implementation of the AbstractBattery class """

    _FILES = {
        "sys_power_supply": Path("/sys/class/power_supply"),
    }

    @staticmethod
    def _post_import_hook(plugin):
        return Battery._detect_battery()

    @property
    @abstractmethod
    def _current(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def _full(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def _drain(self):
        """ Abstract current class to be implemented """

    @property
    @lru_cache(maxsize=1)
    def _status(self):
        """ Returns cached battery status file """
        bat_dir = Battery._directory()
        if bat_dir is None:
            LOG.debug("unable to find battery directory")
            return None

        status_path = bat_dir.joinpath("status")
        status = open_read(status_path)
        if status is None:
            LOG.debug("unable to read battery status file '%s'", status_path)
            return None

        status = status.strip()
        return status

    @property
    @lru_cache(maxsize=1)
    def _current_charge(self):
        """ Returns cached battery current charge file """
        bat_dir = Battery._directory()
        current_filename = self._current

        if bat_dir is None:
            LOG.debug("unable to find battery directory")
            return None

        if current_filename is None:
            LOG.debug("unable to get battery charge current filename")
            return None

        current_path = bat_dir.joinpath(current_filename)
        current_charge = open_read(current_path)
        if current_charge is None:
            LOG.debug("unable to read battery current charge file '%s'",
                      current_path)
            return None

        current_charge = current_charge.strip()
        if not current_charge.isnumeric():
            LOG.debug("unable to read battery current charge file '%s'",
                      current_path)
            return None

        current_charge = int(current_charge)
        return current_charge

    @property
    @lru_cache(maxsize=1)
    def _full_charge(self):
        """ Returns cached battery full charge file """
        bat_dir = Battery._directory()
        full_filename = self._full

        if bat_dir is None:
            LOG.debug("unable to find battery directory")
            return None

        if full_filename is None:
            LOG.debug("unable to get battery charge full filename")
            return None

        full_path = bat_dir.joinpath(full_filename)
        full_charge = open_read(full_path)
        if full_charge is None:
            LOG.debug("unable to read battery full charge file '%s'",
                      full_path)
            return None

        full_charge = full_charge.strip()
        if not full_charge.isnumeric():
            LOG.debug("unable to read battery full charge file '%s'",
                      full_path)
            return None

        full_charge = int(full_charge)
        return full_charge

    @property
    @lru_cache(maxsize=1)
    def _drain_rate(self):
        """ Returns cached battery drain rate file """
        bat_dir = Battery._directory()
        drain_filename = self._drain

        if bat_dir is None:
            LOG.debug("unable to find battery directory")
            return None

        if drain_filename is None:
            LOG.debug("unable to get battery rate drain filename")
            return None

        drain_path = bat_dir.joinpath(drain_filename)
        drain_rate = open_read(drain_path)
        if drain_rate is None:
            LOG.debug("unable to read battery drain rate file '%s'",
                      drain_path)
            return None

        drain_rate = drain_rate.strip()
        if not drain_rate.isnumeric():
            LOG.debug("unable to read battery drain rate file '%s'",
                      drain_path)
            return None

        drain_rate = int(drain_rate)
        return drain_rate

    @lru_cache(maxsize=1)
    def _compare_status(self, query):
        """ Compares status to query """
        bat_dir = Battery._directory()
        if bat_dir is not None:
            return self._status == query
        return None

    def is_present(self, options=None):
        return Battery._directory() is not None

    def is_charging(self, options=None):
        return self._compare_status("Charging")

    def is_full(self, options=None):
        return self._compare_status("Full")

    def _percent(self):
        return self._current_charge, self._full_charge

    def _time(self):
        if not self.is_present or not self._drain_rate:
            return 0

        charge = self._current_charge
        if self.is_charging():
            charge = self._full_charge - charge

        remaining = int((charge / self._drain_rate) * 3600)
        return remaining

    def _power(self):
        pass

    @staticmethod
    @lru_cache(maxsize=1)
    def _directory():
        """ Returns the path for the battery directory """
        def check(_file):
            _file = _file.joinpath("present")
            if not _file.exists():
                return False

            _file_contents = open_read(_file)
            if (
                    _file_contents is None
                    or not _file_contents.strip().isnumeric()
            ):
                return False

            return bool(int(_file_contents))

        _dir = Battery._FILES["sys_power_supply"]
        _dir_glob = _dir.glob("*BAT*")
        bat_dir = next(filter(check, _dir_glob), None)
        return bat_dir

    @staticmethod
    @lru_cache(maxsize=1)
    def _detect_battery():
        """
        Linux stores battery information in /sys/class/power_supply However,
        depending on the machine/driver it may store different information.

        Example:

            On one machine it might contain these files:
                /sys/class/power_supply/charge_now
                /sys/class/power_supply/charge_full
                /sys/class/power_supply/current_now

            On another it might contain these files:
                /sys/class/power_supply/energy_now
                /sys/class/power_supply/energy_full
                /sys/class/power_supply/power_now

        So the purpose of this method is to determine which implementation it
        should use
        """
        bat_dir = Battery._directory()
        if bat_dir is None:
            return BatteryStub

        avail = {
            bat_dir.joinpath("charge_now"): BatteryAmp,
            bat_dir.joinpath("energy_now"): BatteryWatt,
        }

        return next((v for k, v in avail.items() if k.exists()),
                    BatteryStub)


class BatteryAmp(Battery):
    """ Sub-Battery class for systems that stores battery info in amps """

    @property
    @lru_cache(maxsize=1)
    def _current(self):
        """ Returns current charge filename """
        return "charge_now"

    @property
    @lru_cache(maxsize=1)
    def _full(self):
        """ Returns full charge filename """
        return "charge_full"

    @property
    @lru_cache(maxsize=1)
    def _drain(self):
        """ Returns current filename """
        return "current_now"

    def _power(self):
        bat_dir = Battery._directory()
        if bat_dir is None:
            LOG.debug("unable to find battery directory")
            return None

        voltage_path = bat_dir.joinpath("voltage_now")
        voltage = open_read(voltage_path)
        drain_rate = self._drain_rate

        if voltage is None:
            LOG.debug("unable to read battery voltage file '%s'", voltage)
            return None

        voltage = voltage.strip()
        if not voltage.isnumeric():
            LOG.debug("unable to read battery voltage file '%s'", voltage)
            return None

        if drain_rate is None:
            return None

        voltage = int(voltage)
        power = (drain_rate * voltage) / 1_000_000_000_000
        return power


class BatteryWatt(Battery):
    """ Sub-Battery class for systems that stores battery info in watt """

    @property
    @lru_cache(maxsize=1)
    def _current(self):
        """ Returns current energy filename """
        return "energy_now"

    @property
    @lru_cache(maxsize=1)
    def _full(self):
        """ Returns full energy filename """
        return "energy_full"

    @property
    @lru_cache(maxsize=1)
    def _drain(self):
        """ Returns power filename """
        return "power_now"

    def _power(self):
        drain_rate = self._drain_rate
        if drain_rate is None:
            return None
        return drain_rate / 1_000_000
