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
# pylint: disable=no-self-use,too-many-lines

""" Abstract classes for getting system info """

import os
import re
import time

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from functools import lru_cache, reduce
from importlib import import_module
from logging import getLogger, DEBUG
from pathlib import Path

from ..tools.storage import Storage
from ..tools.utils import (percent, run, unix_epoch_to_str, round_trim,
                           trim_string, namespace_types_as_dict)
from ..tools.df import DfEntry


LOG = getLogger(__name__)


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
    @lru_cache(maxsize=1)
    def _valid_info(self):
        """ Returns list of info in getter """
        def check(i):
            reserved = ["query", "all_info"]
            return (
                not i.startswith("_")
                and i not in reserved
                and callable(getattr(self, i))
            )

        info = list(filter(check, dir(self)))
        LOG.debug("valid info for '%s': %s", self.domain_name, info)
        return info

    def query(self, info, options_string):
        """ Returns the value of info """
        LOG.debug("querying domain '%s' for info '%s'", self.domain_name, info)
        LOG.debug("options string: %s", options_string)

        if info not in self._valid_info:
            msg = f"info name '{info}' is not in domain"
            raise RuntimeError(msg)

        if options_string is None:
            LOG.debug("options string is empty, using default options")
            options = self.default_options
        else:
            LOG.debug("parsing options string '%s'", options_string)
            options = self._parse_options(info, options_string)

        if LOG.isEnabledFor(DEBUG):
            msg = (
                f"begin querying domain '{self.domain_name}' for info '{info}'"
            )

            LOG.debug("=" * len(msg))
            LOG.debug(msg)
            LOG.debug("=" * len(msg))

        val = self._query(info, options)

        if LOG.isEnabledFor(DEBUG):
            msg = f"query result for '{self.domain_name}.{info}': '{val}'"
            LOG.debug("=" * len(msg))
            LOG.debug(msg)
            LOG.debug("=" * len(msg))

        return val

    def _query(self, info, options):
        return getattr(self, info)(options)

    def _parse_options(self, info, option_string):
        options = deepcopy(self.default_options)
        option_types = self._option_types
        for o in filter(len, map(trim_string, option_string.split(","))):
            k, v = (o.split("=", 1) + [None, None])[:2]

            LOG.debug("option_key=%s, option_value=%s", k, v)

            try:
                LOG.debug("getting type for option '%s'", k)
                option_type = reduce(dict.__getitem__, [info, k], option_types)
                LOG.debug("type for option '%s' is '%s'", k,
                          option_type.__name__)
            except (KeyError, TypeError):
                LOG.debug(
                    "option '%s' does not exist, passing it to handler...",
                    k
                )

                try:
                    if v is None:
                        self._handle_missing_option_value(options, info, o)
                        LOG.debug("option successfully handled")
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

    def all_info(self):
        """ Returns a generator object for getting all info in this domain """
        for i in self._valid_info:
            yield i, self.query(i, None)


class AbstractMultipleValuesGetter(AbstractGetter):
    """
    Specialised Abstract Getter class where it is able to query multiple items
    """

    def _query(self, info, options):
        val = super(AbstractMultipleValuesGetter, self)._query(info, options)
        if not isinstance(val, dict):
            return None

        if hasattr(options, "index"):
            key = options.index
        else:
            key = next(iter(val.keys()), None)

        return val.get(key, None)

    def _handle_missing_option_value(self, options, info, option_name):
        setattr(options, "index", option_name)


class AbstractStorage(AbstractGetter):
    """
    AbstractStorage for info that fetches used, total and percent attributes
    """

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
        if value is None or prefix is None:
            used = Storage(value=0, prefix="B", rounding="0")
        else:
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

        if value is None or prefix is None:
            total = Storage(value=0, prefix="B", rounding="0")
        else:
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
            LOG.debug("unable to get cpu speed, using fallback speed")
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
        if load is None:
            LOG.debug("unable to get load")
            return None

        if options.load_avg.short:
            return load[0]

        return " ".join(load)

    def cpu_usage(self, options=None):
        """ Cpu usage method """
        if options is None:
            options = self.default_options

        cores = self.cores(options)
        ps_cmd = ["ps", "-e", "-o", "%cpu"]
        ps_out = run(ps_cmd)

        if not ps_out:
            LOG.debug("unable to get ps output")
            return None

        ps_out = ps_out.strip().splitlines()[1:]
        cpu_usage = sum(map(float, ps_out)) / cores
        cpu_usage = round_trim(cpu_usage, options.cpu_usage.round)
        return cpu_usage

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
        if temp is None:
            LOG.debug("unable to get temp output")
            return None

        temp = round_trim(temp, options.temp.round)
        return temp

    @abstractmethod
    def _uptime(self):
        """ Abstract uptime method to be implemented by subclass """

    def uptime(self, options=None):
        """ Uptime method """
        uptime = self._uptime()
        if uptime is None:
            LOG.debug("unable to get uptime")
            return None

        uptime = unix_epoch_to_str(uptime)
        return uptime


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

    def _handle_missing_option_value(self, options, info, option_name):
        if option_name not in options.query:
            options.query = tuple(list(options.query) + [option_name])

        if not Path(option_name).is_block_device():
            LOG.debug("disk index is a mount, attempting to get device...")

            dev = self._mount_to_devname(options, option_name)
            if dev is None:
                LOG.debug("unable to get device")
            else:
                LOG.debug("'%s' is '%s'", option_name, dev)
            option_name = dev

        super(AbstractDisk, self)._handle_missing_option_value(options, info,
                                                               option_name)

    def _mount_to_devname(self, options, mount_path):
        mounts = self.mount(options)
        target = next((k for k, v in mounts.items() if mount_path == v), None)
        return target

    @property
    @abstractmethod
    def _DF_FLAGS(self):
        pass

    @property
    @lru_cache(maxsize=1)
    def _df(self):
        df_out = run(self._DF_FLAGS)

        if not df_out:
            return None

        df_out = df_out.strip().splitlines()[1:]
        return df_out

    @lru_cache(maxsize=1)
    def _df_query(self, query):
        """ Return df entries """
        disks = list()
        mounts = list()

        if not query:
            LOG.debug("df query is empty, defaulting to '/'")
            mounts.append(r"/")
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
        reg = r"|".join(reg)
        LOG.debug("df query regex is '%s'", reg)
        reg = re.compile(reg)

        results = dict()
        if self._df is None:
            LOG.debug("unable to get df output")
            return results

        for i in filter(reg.search, self._df):
            split = i.split()
            if split[0] in results.keys():
                continue

            df_entry = DfEntry(*split)
            results[df_entry.filesystem] = df_entry

        return results

    def _original_dev(self, options=None):
        """ Disk device without modification """
        if options is None:
            query = tuple()
        else:
            query = options.query

        df = self._df_query(query)
        if df is None:
            return None

        dev = {k: v.filesystem for k, v in df.items()}
        return dev

    def dev(self, options=None):
        """ Disk device method """
        if options is None:
            options = self.default_options

        dev = self._original_dev(options)

        if dev is None:
            return None

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

        df = self._df_query(query)
        if df is None:
            return None

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

        df = self._df_query(query)
        if df is None:
            return None

        used = dict()
        for k, v in df.items():
            stor = Storage(int(v.used), prefix="KiB",
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

        df = self._df_query(query)
        if df is None:
            return None

        total = dict()
        for k, v in df.items():
            stor = Storage(int(v.blocks), prefix="KiB",
                           rounding=options.total.round)
            stor.prefix = options.total.prefix
            total[k] = stor

        return total

    def percent(self, options=None):
        """ Disk percent property """
        if options is None:
            options = self.default_options

        devs = self._original_dev(options)
        if devs is None:
            return None

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


class AbstractNetwork(AbstractGetter):
    """ Abstract network class to be implemented by subclass """

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
        cmd, reg = self._ssid()
        if cmd is None or reg is None:
            return None

        out = run(cmd)
        if not out:
            return None

        ssid = (reg.match(i.strip()) for i in out.splitlines())
        ssid = next((i.group(1) for i in ssid if i), None)
        return ssid

    def local_ip(self, options=None):
        """ Network local ip method """
        dev = self.dev(options)
        if dev is None:
            return None

        reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
        ip_out = run(self._LOCAL_IP_CMD + [dev])
        if not ip_out:
            return None

        ip_out = ip_out.strip().splitlines()
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
        bytes_rate = self._bytes_rate(dev, "down")
        download = Storage(bytes_rate, prefix="B",
                           rounding=options.download.round)
        download.prefix = options.download.prefix
        return download

    def upload(self, options=None):
        """ Network upload method """
        if options is None:
            options = self.default_options

        dev = self.dev(options)
        bytes_rate = self._bytes_rate(dev, "up")
        upload = Storage(bytes_rate, prefix="B",
                         rounding=options.upload.round)
        upload.prefix = options.upload.prefix
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

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

        if LOG.isEnabledFor(DEBUG):
            msg = "Initialising System with: %s"
            sys_debug = {k: f"{v.__module__}.{v.__name__}"
                         for k, v in kwargs.items()}
            LOG.debug(msg, sys_debug)

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
        LOG.debug("os_name is %s", os_name)

        # Module system files format is the output of "uname -s" in lowercase
        mod_prefix = __name__.split(".")[:-1]
        mod_name = ".".join(mod_prefix + [os_name.lower()])
        system = None

        try:
            LOG.debug("importing module '%s'...", mod_name)
            mod = import_module(mod_name)
            LOG.debug("imported module '%s'", mod_name)

            system = getattr(mod, os_name)(default_options)
        except ModuleNotFoundError:
            LOG.error("Unknown system: '%s'", os_name)
            LOG.error("Exiting...")

        return system

    def detect_window_manager(self):
        """ Detects which supported window manager is currently running """
        ps_out = run(["ps", "ax", "-e", "-o", "command"])

        if not ps_out:
            return WindowManagerStub

        return next((v for k, v in self._SUPPORTED_WMS.items() if k in ps_out),
                    WindowManagerStub)

    def query(self, domain):
        """ Queries a system for a domain and info """
        LOG.debug("querying system for domain '%s'", domain)

        if domain not in self._getters.keys():
            msg = f"domain name '{domain}' not in system"
            raise RuntimeError(msg)

        if self._getters_cache[domain] is None:
            LOG.debug("domain '%s' is not initialised. Initialising...",
                      domain)
            opts = self.default_options[domain]
            self._getters_cache[domain] = self._getters[domain](domain, opts)

        return self._getters_cache[domain]
