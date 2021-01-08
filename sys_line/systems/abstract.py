#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=invalid-name,too-few-public-methods,unused-argument
# pylint: disable=no-self-use

""" Abstract classes for getting system info """

import os
import re
import sys
import time

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from functools import lru_cache, reduce
from importlib import import_module
from pathlib import Path

from ..tools.storage import Storage
from ..tools.utils import (percent, run, unix_epoch_to_str, round_trim,
                           trim_string, namespace_types_as_dict)
from ..tools.df import DfEntry


class AbstractGetter(ABC):
    """
    Abstract Getter class to store both options and the implementations for the
    information under the getter
    """

    def __init__(self, domain_name, default_options):
        super(AbstractGetter, self).__init__()

        self.domain_name = domain_name
        self.default_options = default_options

    @property
    @lru_cache(maxsize=1)
    def _option_types(self):
        return namespace_types_as_dict(self.default_options)

    @property
    @abstractmethod
    def _valid_info(self):
        """ Returns list of info in getter """

    def query(self, info, options_string):
        """ Returns the value of info """
        if info not in self._valid_info:
            msg = f"info name '{info}' is not in domain"
            raise RuntimeError(msg)

        if options_string is None:
            options = self.default_options
        else:
            options = self._parse_options(info, options_string)

        return self._query(info, options)

    def _query(self, info, options):
        return getattr(self, info)(options)

    def _parse_options(self, info, option_string):
        options = deepcopy(self.default_options)
        option_types = self._option_types
        for o in filter(len, map(trim_string, option_string.split(","))):
            k, v = (o.split("=", 1) + [None, None])[:2]

            try:
                option_type = reduce(dict.__getitem__, [info, k], option_types)
            except (KeyError, TypeError):
                try:
                    if v is None:
                        self._handle_missing_option_value(options, info, o)
                        continue
                except NotImplementedError:
                    pass

                msg = f"no such option in domain: {o}"
                raise RuntimeError(msg)

            if v is None and option_type is bool:
                v = True

            if k == "prefix" and v not in Storage.PREFIXES:
                msg = f"invalid value for prefix: {v}"
                raise RuntimeError(msg)

            try:
                setattr(getattr(options, info), k, option_type(v))
            except ValueError:
                msg = (
                    f"invalid type for option '{k}': "
                    f"expecting {option_type.__name__}, "
                    f"got {type(v).__name__}"
                )
                raise RuntimeError(msg)

        return options

    def _handle_missing_option_value(self, options, info, option_name):
        raise NotImplementedError()

    def __str__(self):
        """ The string representation of the getter would return all values """
        return "\n".join([
            f"{self.domain_name}.{i}: {getattr(self, i)(self.default_options)}"
            for i in self._valid_info
        ])


class AbstractMultipleValuesGetter(AbstractGetter):
    """
    Specialised Abstract Getter class where it is able to query multiple items
    """

    def _query(self, info, options):
        val = super(AbstractMultipleValuesGetter, self)._query(info, options)
        if isinstance(val, dict):
            if hasattr(options, "index"):
                key = options.index
            else:
                key = next(iter(val.keys()), None)
            val = val.get(key, None)
        return val

    def _handle_missing_option_value(self, options, info, option_name):
        setattr(options, "index", option_name)


class AbstractStorage(AbstractGetter):
    """
    AbstractStorage for info that fetches used, total and percent attributes
    """

    @property
    def _valid_info(self):
        return ["used", "total", "percent"]

    @abstractmethod
    def _used(self):
        """
        Abstract used method that returns Storage arguments to be implemented
        by subclass
        """

    def used(self, options=None):
        """
        Returns a Storage class representing the amount used in storage
        """
        if options is None:
            options = self.default_options

        value, prefix = self._used()
        used = Storage(value=value, prefix=prefix,
                       rounding=options.used.round)
        used.prefix = options.used.prefix
        return used

    @abstractmethod
    def _total(self):
        """
        Abstract total method that returns Storage arguments to be implemented
        by subclass
        """

    def total(self, options=None):
        """
        Returns a Storage class representing the total amount in storage
        """
        if options is None:
            options = self.default_options

        value, prefix = self._total()
        total = Storage(value=value, prefix=prefix,
                        rounding=options.total.round)
        total.prefix = options.total.prefix
        return total

    def percent(self, options=None):
        """ Abstract percent property """
        if options is None:
            options = self.default_options

        used = self.used(options)
        total = self.total(options)
        perc = percent(used.bytes, total.bytes)
        if perc is None:
            perc = 0.0
        else:
            perc = round_trim(perc, options.percent.round)
        return perc


class AbstractCpu(AbstractGetter):
    """ Abstract cpu class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["cores", "cpu", "load_avg", "cpu_usage", "fan", "temp",
                "uptime"]

    @abstractmethod
    def cores(self, options=None):
        """ Abstract cores method to be implemented by subclass """

    @abstractmethod
    def _cpu_string(self):
        """
        Private abstract cpu string method to be implemented by subclass
        """

    @abstractmethod
    def _cpu_speed(self):
        """
        Private abstract cpu speed method to be implemented by subclass
        """

    def cpu(self, options=None):
        """ Returns cpu string """
        cpu_reg = re.compile(r"\s+@\s+(\d+\.)?\d+GHz")
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        cores = self.cores(options)
        cpu = self._cpu_string()
        speed = self._cpu_speed()
        cpu = trim_reg.sub("", cpu.strip())

        if speed is not None:
            fmt = fr" ({cores}) @ {speed}GHz"
            cpu = cpu_reg.sub(fmt, cpu)
        else:
            fmt = fr"({cores}) @"
            cpu = re.sub(r"@", fmt, cpu)

        cpu = re.sub(r"\s+", " ", cpu)

        return cpu

    @abstractmethod
    def _load_avg(self):
        """ Abstract load average method to be implemented by subclass """

    def load_avg(self, options=None):
        """ Load average method """
        if options is None:
            options = self.default_options

        load = self._load_avg()
        if load is not None:
            load = load[0] if options.load_avg.short else " ".join(load)
        return load

    def cpu_usage(self, options=None):
        """ Cpu usage method """
        if options is None:
            options = self.default_options

        cores = self.cores(options)
        ps_out = run(["ps", "-e", "-o", "%cpu"]).strip().split("\n")[1:]
        cpu_usage = sum(float(i) for i in ps_out) / cores
        return round_trim(cpu_usage, options.cpu_usage.round)

    @abstractmethod
    def fan(self, options=None):
        """ Abstract fan method to be implemented by subclass """

    @abstractmethod
    def _temp(self):
        """ Abstract temperature method to be implemented by subclass """

    def temp(self, options=None):
        """ Temperature method """
        if options is None:
            options = self.default_options

        temp = self._temp()
        if temp is not None:
            return round_trim(temp, options.temp.round)
        return None

    @abstractmethod
    def _uptime(self):
        """ Abstract uptime method to be implemented by subclass """

    def uptime(self, options=None):
        """ Uptime method """
        return unix_epoch_to_str(self._uptime())


class AbstractMemory(AbstractStorage):
    """ Abstract memory class to be implemented by subclass """

    @abstractmethod
    def _used(self):
        pass

    @abstractmethod
    def _total(self):
        pass


class AbstractSwap(AbstractStorage):
    """ Abstract swap class to be implemented by subclass """

    @abstractmethod
    def _used(self):
        pass

    @abstractmethod
    def _total(self):
        pass


class AbstractDisk(AbstractStorage, AbstractMultipleValuesGetter):
    """ Abstract disk class to be implemented by subclass """

    @property
    def _valid_info(self):
        return super(AbstractDisk, self)._valid_info + ["dev", "mount",
                                                        "name", "partition"]

    def _handle_missing_option_value(self, options, info, option_name):
        if option_name not in options.query:
            options.query = tuple(list(options.query) + [option_name])

        if not Path(option_name).is_block_device():
            option_name = self._mount_to_devname(options, option_name)

        super(AbstractDisk, self)._handle_missing_option_value(options, info,
                                                               option_name)

    def _mount_to_devname(self, options, mount_path):
        return next(k for k, v in self.mount(options).items()
                    if mount_path == v)

    @property
    @abstractmethod
    def _DF_FLAGS(self):
        pass

    @property
    @lru_cache(maxsize=1)
    def _df(self):
        return run(self._DF_FLAGS).strip().split("\n")[1:]

    @lru_cache(maxsize=1)
    def _df_query(self, query):
        """ Return df entries """
        results = dict()
        disks = list()
        mounts = list()
        if not query:
            mounts.append("/")
        else:
            for p in filter(Path.exists, map(Path, query)):
                if p.is_block_device():
                    disks.append(str(p.resolve()))
                else:
                    mounts.append(str(p.resolve()))

        reg = list()
        if disks:
            disks = r"|".join(disks)
            reg.append(fr"^({disks})")
        if mounts:
            mounts = r"|".join(mounts)
            reg.append(fr"({mounts})$")
        reg = re.compile(r"|".join(reg))

        if self._df is not None:
            for i in filter(reg.search, self._df):
                split = i.split()
                if split[0] not in results.keys():
                    df_entry = DfEntry(*split)
                    results[df_entry.filesystem] = df_entry

        return results

    def _original_dev(self, options=None):
        """ Disk device without modification """
        if options is None:
            query = tuple()
        else:
            query = options.query

        dev = None
        df = self._df_query(query)
        if df is not None:
            dev = {k: v.filesystem for k, v in df.items()}
        return dev

    def dev(self, options=None):
        """ Disk device method """
        if options is None:
            options = self.default_options

        dev = self._original_dev(options)
        if options.dev.short:
            dev = {k: v.split("/")[-1] for k, v in dev.items()}
        return dev

    @abstractmethod
    def name(self, options=None):
        """ Abstract disk name method to be implemented by subclass """

    def mount(self, options=None):
        """ Disk mount method """
        if options is None:
            query = tuple()
        else:
            query = options.query

        mount = None
        df = self._df_query(query)
        if df is not None:
            mount = {k: v.mount for k, v in df.items()}
        return mount

    @abstractmethod
    def partition(self, options=None):
        """ Abstract disk partition method to be implemented by subclass """

    def _used(self):
        pass

    def used(self, options=None):
        """ Disk used method """
        if options is None:
            options = self.default_options
            query = tuple()
        else:
            query = options.query

        used = None
        df = self._df_query(query)
        if df is not None:
            used = dict()
            for k, v in df.items():
                stor = Storage(int(v.used), "KiB",
                               rounding=options.used.round)
                stor.prefix = options.used.prefix
                used[k] = stor
        return used

    def _total(self):
        pass

    def total(self, options=None):
        """ Disk total method """
        if options is None:
            options = self.default_options
            query = tuple()
        else:
            query = options.query

        total = None
        df = self._df_query(query)
        if df is not None:
            total = dict()
            for k, v in df.items():
                stor = Storage(int(v.blocks), "KiB",
                               rounding=options.total.round)
                stor.prefix = options.total.prefix
                total[k] = stor
        return total

    def percent(self, options=None):
        """ Disk percent property """
        if options is None:
            options = self.default_options

        perc = None
        devs = self._original_dev(options)
        if devs is not None:
            perc = dict()
            used = self.used(options)
            total = self.total(options)
            for dev in devs.keys():
                value = percent(used[dev].bytes, total[dev].bytes)
                if value is None:
                    value = 0.0
                else:
                    value = round_trim(value, options.percent.round)
                perc[dev] = value
        return perc


class AbstractBattery(AbstractGetter):
    """ Abstract battery class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["is_present", "is_charging", "is_full", "percent",
                "time", "power"]

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

        perc = None
        if self.is_present(options):
            current, full = self._percent()
            if current is not None and full is not None:
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

        power = None
        if self.is_present(options):
            power = self._power()
            if power is not None:
                power = round_trim(power, options.power.round)
        return power


class AbstractNetwork(AbstractGetter):
    """ Abstract network class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["dev", "ssid", "local_ip", "download", "upload"]

    @property
    @abstractmethod
    def _LOCAL_IP_CMD(self):
        pass

    @lru_cache(maxsize=1)
    @abstractmethod
    def dev(self, options=None):
        """ Abstract network device method to be implemented by subclass """

    @abstractmethod
    def _ssid(self):
        """ Abstract ssid resource method to be implemented by subclass """

    def ssid(self, options=None):
        """ Network ssid method """
        ssid = None
        cmd, reg = self._ssid()
        if not (cmd is None or reg is None):
            ssid = (reg.match(i.strip()) for i in run(cmd).split("\n"))
            ssid = next((i.group(1) for i in ssid if i), None)

        return ssid

    def local_ip(self, options=None):
        """ Network local ip method """
        ip_out = None
        dev = self.dev(options)
        if dev is not None:
            reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
            ip_out = run(self._LOCAL_IP_CMD + [dev]).strip().split("\n")
            ip_out = (reg.match(line.strip()) for line in ip_out)
            ip_out = next((i.group(1) for i in ip_out if i), None)
        return ip_out

    @abstractmethod
    def _bytes_delta(self, dev, mode):
        """
        Abstract network bytes delta method to fetch the change in bytes on
        a device depending on mode
        """

    def _bytes_rate(self, dev, mode):
        """
        Abstract network bytes rate method to fetch the rate of change in bytes
        on a device depending on mode
        """
        if dev is None:
            return 0.0

        start = self._bytes_delta(dev, mode)
        start_time = time.time()

        # Timeout after 2 seconds
        while (self._bytes_delta(dev, mode) <= start and
               time.time() - start_time < 2):
            time.sleep(0.01)

        end = self._bytes_delta(dev, mode)
        if end == start:
            return 0.0

        end_time = time.time()
        delta_bytes = end - start
        delta_time = end_time - start_time

        return delta_bytes / delta_time

    def download(self, options=None):
        """ Network download method """
        if options is None:
            options = self.default_options

        dev = self.dev(options)
        download = Storage(self._bytes_rate(dev, "down"), "B",
                           rounding=options.download.round)
        download.prefix = options.download.prefix
        return download

    def upload(self, options=None):
        """ Network upload method """
        if options is None:
            options = self.default_options

        dev = self.dev(options)
        upload = Storage(self._bytes_rate(dev, "up"), "B",
                         rounding=options.upload.round)
        upload.prefix = options.upload.prefix
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

    @property
    def _valid_info(self):
        return ["date", "time"]

    @staticmethod
    def _format(fmt):
        """ Wrapper for printing date and time format """
        return "{{:{}}}".format(fmt).format(datetime.now())

    def date(self, options=None):
        """ Returns the date as a string from a specified format """
        if options is None:
            options = self.default_options

        return Date._format(options.date.format)

    def time(self, options=None):
        """ Returns the time as a string from a specified format """
        if options is None:
            options = self.default_options

        return Date._format(options.time.format)


class AbstractWindowManager(AbstractGetter):
    """ Abstract window manager class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["desktop_index", "desktop_name", "app_name", "window_name"]

    @abstractmethod
    def desktop_index(self, options=None):
        """ Abstract desktop index method to be implemented by subclass """

    @abstractmethod
    def desktop_name(self, options=None):
        """ Abstract desktop name method to be implemented by subclass """

    @abstractmethod
    def app_name(self, options=None):
        """
        Abstract focused application name method to be implemented by subclass
        """

    @abstractmethod
    def window_name(self, options=None):
        """
        Abstract focused window name method to be implemented by subclass
        """


class AbstractMisc(AbstractGetter):
    """ Misc class for fetching miscellaneous information """

    @property
    def _valid_info(self):
        return ["vol", "scr"]

    @abstractmethod
    def _vol(self):
        """ Abstract volume method to be implemented by subclass """

    def vol(self, options=None):
        """ Volume method """
        if options is None:
            options = self.default_options

        vol = self._vol()
        if vol is not None:
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
        scr = round_trim(scr, options.scr.roun)
        return scr


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


class WindowManagerStub(AbstractWindowManager):
    """ Placeholder window manager """

    def desktop_index(self, options=None):
        return None

    def desktop_name(self, options=None):
        return None

    def app_name(self, options=None):
        return None

    def window_name(self, options=None):
        return None


class System(ABC):
    """
    Abstract System class to store all the assigned getters from the sub class
    that implements this class
    """

    DOMAINS = ("cpu", "memory", "swap", "disk",
               "battery", "network", "date", "window manager", "misc")
    SHORT_DOMAINS = ("cpu", "mem", "swap", "disk",
                     "bat", "net", "date", "wm", "misc")

    def __init__(self, default_options, **kwargs):
        super(System, self).__init__()
        self._getters = dict(kwargs, date=Date)
        self.default_options = {
            k: getattr(default_options, k, None) for k in self._getters
        }
        self._getters_cache = {k: None for k in self._getters}

    @property
    @abstractmethod
    def _SUPPORTED_WMS(self):
        """
        Abstract property containing the list of supported window managers for
        this system
        """

    @staticmethod
    def create_instance(default_options):
        """
        Instantialises an implementation of the System class by dynamically
        importing the module
        """
        os_name = os.uname().sysname

        # Module system files format is the output of "uname -s" in lowercase
        mod_prefix = __name__.split(".")[:-1]
        mod_name = ".".join(mod_prefix + [os_name.lower()])
        system = None

        try:
            mod = import_module(mod_name)
            system = getattr(mod, os_name)(default_options)
        except ModuleNotFoundError:
            print(f"Unknown system: '{os_name}'", "Exiting...",
                  sep="\n", file=sys.stderr)

        return system

    def detect_window_manager(self):
        """ Detects which supported window manager is currently running """
        ps_out = run(["ps", "ax", "-e", "-o", "command"])
        return next((v for k, v in self._SUPPORTED_WMS.items() if k in ps_out),
                    WindowManagerStub)

    def query(self, domain):
        """ Queries a system for a domain and info """
        if domain not in self._getters.keys():
            msg = f"domain name '{domain}' not in system"
            raise RuntimeError(msg)

        if self._getters_cache[domain] is None:
            opts = self.default_options[domain]
            self._getters_cache[domain] = self._getters[domain](domain, opts)

        return self._getters_cache[domain]
