#!/usr/bin/env python3
# pylint: disable=abstract-class-instantiated
# pylint: disable=abstract-method
# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=pointless-string-statement
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments

""" Abstract classes for getting system info """

import re
import time

from abc import ABC, abstractmethod
from copy import copy
from datetime import datetime
from functools import lru_cache
from pathlib import Path as p

from ..tools.storage import Storage
from ..tools.utils import percent, run, unix_epoch_to_str, _round
from ..tools.df import DfEntry


class AbstractGetter(ABC):
    """
    Abstract Getter class to store both options and any auxilary classes
    """

    def __init__(self, domain_name, options, aux = None):
        super(AbstractGetter, self).__init__()

        self.domain_name = domain_name
        self.options = options
        self.aux = aux

    def query(self, info, options):
        if info not in self._valid_info:
            raise RuntimeError("info name not in domain")
        return self._query(info, options)

    def _query(self, info, options):
        if options is None:
            val = getattr(self, info)
        else:
            # Copy current options to tmp
            tmp = copy(self.options)

            # Set options and get value
            for k, v in self._parse_options(info, options).items():
                setattr(self.options, k, v)
            val = getattr(self, info)

            # Restore options
            self.options = tmp
        return val

    def _parse_options(self, info, options):
        opts = dict()
        if options:
            for i in options.split(","):
                if not i:
                    continue

                # An option with "=" requires a value, unless it is a boolean
                # option
                if "=" not in i:
                    if hasattr(self.options, i):
                        if isinstance(getattr(self.options, i), bool):
                            i = "{}=True".format(i)
                        else:
                            err = "option requires value: {}".format(i)
                            raise RuntimeError(err)
                    else:
                        err = "no such option in domain: {}".format(i)
                        raise RuntimeError(err)

                k, v = i.split("=", 1)

                # A prefix option needs to be one of the prefixes
                if k == "prefix":
                    if v not in Storage.PREFIXES:
                        err = "invalid value for prefix: {}".format(v)
                        raise RuntimeError(err)

                if (hasattr(self.options, k) or
                    hasattr(self.options, "{}_{}".format(info, k))):
                    # Boolean options does not require the info name as part of
                    # the option
                    if v in ["True", "False"]:
                        v = v == "True"
                        key = k
                    else:
                        if v.isnumeric():
                            v = int(v)
                        key = "{}_{}".format(info, k)
                    opts[key] = v
                else:
                    err = "no such option in domain: {}".format(i)
                    raise RuntimeError(err)

        return opts

    def __str__(self):
        """ The string representation of the getter would return all values """
        return "\n".join([
            "{}.{}: {}".format(self.domain_name, i, getattr(self, i))
            for i in self._valid_info
        ])

    @property
    @abstractmethod
    def _valid_info(self):
        """ Returns list of info in getter """


class AbstractStorage(AbstractGetter):
    """
    AbstractStorage for info that fetches used, total and percent attributes
    """

    def __init__(self, domain_name, options, aux):
        super(AbstractStorage, self).__init__(domain_name, options, aux=aux)

    @property
    def _valid_info(self):
        return ["used", "total", "percent"]

    @abstractmethod
    def _used(self):
        """
        Abstract used method that returns Storage arguments to be implemented
        by subclass
        """
        pass

    @property
    def used(self):
        value, prefix = self._used()
        used = Storage(value=value, prefix=prefix,
                       rounding=self.options.used_round)
        used.prefix = self.options.used_prefix
        return used

    @abstractmethod
    def _total(self):
        """
        Abstract total method that returns Storage arguments to be implemented
        by subclass
        """
        pass

    @property
    def total(self):
        value, prefix = self._total()
        total = Storage(value=value, prefix=prefix,
                        rounding=self.options.total_round)
        total.prefix = self.options.total_prefix
        return total

    @property
    def percent(self):
        """ Abstract percent property """
        perc = percent(self.used.value, self.total.value)
        perc = 0.0 if perc is None else _round(perc, self.options.percent_round)
        return perc


class AbstractCpu(AbstractGetter):
    """ Abstract cpu class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["cores", "cpu", "load_avg",
                "cpu_usage", "fan", "temp", "uptime"]

    @property
    @abstractmethod
    def cores(self):
        """ Abstract cores method to be implemented by subclass """

    @abstractmethod
    def _cpu_speed(self):
        """
        Private abstract cpu and speed method to be implemented by subclass
        """

    @property
    def cpu(self):
        """ Returns cpu string """
        cpu_reg = re.compile(r"\s+@\s+(\d+\.)?\d+GHz")
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        cores = self.cores
        cpu, speed = self._cpu_speed()
        cpu = trim_reg.sub("", cpu.strip())

        if speed is not None:
            fmt = r" ({}) @ {}GHz".format(cores, speed)
            cpu = cpu_reg.sub(fmt, cpu)
        else:
            fmt = r"({}) @".format(cores)
            cpu = re.sub(r"@", fmt, cpu)

        cpu = re.sub(r"\s+", " ", cpu)

        return cpu

    @abstractmethod
    def _load_avg(self):
        """ Abstract load average method to be implemented by subclass """

    @property
    def load_avg(self):
        """ Load average method """
        load = self._load_avg()
        return load[0] if self.options.load_short else " ".join(load)

    @property
    def cpu_usage(self):
        """ Cpu usage method """
        cores = self.cores
        ps_out = run(["ps", "-e", "-o", "%cpu"]).strip().split("\n")[1:]
        cpu_usage = sum([float(i) for i in ps_out]) / cores
        return _round(cpu_usage, self.options.usage_round)

    @property
    @abstractmethod
    def fan(self):
        """ Abstract fan method to be implemented by subclass """

    @property
    @abstractmethod
    def temp(self):
        """ Abstract temperature method to be implemented by subclass """

    @abstractmethod
    def _uptime(self):
        """ Abstract uptime method to be implemented by subclass """

    @property
    def uptime(self):
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


class AbstractDisk(AbstractStorage):
    """ Abstract disk class to be implemented by subclass """

    def __init__(self, domain_name, options, aux):
        super(AbstractDisk, self).__init__(domain_name, options, aux=aux)
        self._df_entries = None

    @property
    def _valid_info(self):
        return super(AbstractDisk, self)._valid_info + ["dev", "mount",
                                                        "name", "partition"]

    def _query(self, info, options):
        # Key for which device to get information from
        key = None
        new_opts = list()

        if options:
            for i in options.split(","):
                if "=" in i:
                    if i.split("=", 1)[0] not in ["disk", "mount"]:
                        new_opts.append(i)
                else:
                    if hasattr(self.options, i):
                        new_opts.append(i)
                    else:
                        key = i
        new_opts = ",".join(new_opts)

        if key is None:
            # Set key to the first available mount or disk. By default, it
            # should be "/" if no disks or mounts are set. Otherwise, it is set
            # to the first disk or mount set in the arguments
            key = next(iter(getattr(self, info)), "/")
        elif not (key in self.options.disk or key in self.options.mount):
            if p(key).is_block_device():
                self.options.disk.append(key)
            else:
                self.options.mount.append(key)

        if not p(key).is_block_device():
            key = self._mount_to_devname(key)

        return super(AbstractDisk, self)._query(info, new_opts)[key]

    def _mount_to_devname(self, mount_path):
        return next(k for k, v in self.mount.items() if mount_path == v)

    @property
    @abstractmethod
    def _DF_FLAGS(self):
        pass

    @property
    @lru_cache(maxsize=1)
    def _df(self):
        return run(self._DF_FLAGS).strip().split("\n")[1:]

    @property
    def df_entries(self):
        """
        Return df entries

        If any modifications to options.disk or options.mount is made,
        _df_entries is updated to reflect these changes
        """
        if self._df_entries is None:
            self._df_entries = dict()

        reg = list()
        if self.options.disk:
            reg.append(r"^({})".format(r"|".join(self.options.disk)))
        if self.options.mount:
            reg.append(r"({})$".format(r"|".join(self.options.mount)))
        reg = re.compile(r"|".join(reg))

        if self._df is not None:
            for i in self._df:
                if reg.search(i):
                    split = i.split()
                    if split[0] not in self._df_entries.keys():
                        df_entry = DfEntry(*split)
                        self._df_entries[df_entry.filesystem] = df_entry

        return self._df_entries

    @property
    def original_dev(self):
        """ Disk device without modification """
        dev = None
        if self.df_entries is not None:
            dev = {k: v.filesystem for k, v in self.df_entries.items()}
        return dev

    @property
    def dev(self):
        """ Disk device method """
        dev = self.original_dev
        if self.options.short_dev:
            dev = {k: v.split("/")[-1] for k, v in dev.items()}
        return dev

    @property
    @abstractmethod
    def name(self):
        """ Abstract disk name method to be implemented by subclass """

    @property
    def mount(self):
        """ Disk mount method """
        mount = None
        if self.df_entries is not None:
            mount = {k: v.mount for k, v in self.df_entries.items()}
        return mount

    @property
    @abstractmethod
    def partition(self):
        """ Abstract disk partition method to be implemented by subclass """

    def _used(self):
        pass

    @property
    def used(self):
        """ Disk used method """
        used = None
        if self.df_entries is not None:
            used = dict()
            for k, v in self.df_entries.items():
                stor = Storage(value=int(v.used), prefix="KiB",
                               rounding=self.options.used_round)
                stor.prefix = self.options.used_prefix
                used[k] = stor
        return used

    def _total(self):
        pass

    @property
    def total(self):
        """ Disk total method """
        total = None
        if self.df_entries is not None:
            total = dict()
            for k, v in self.df_entries.items():
                stor = Storage(value=int(v.blocks), prefix="KiB",
                                rounding=self.options.total_round)
                stor.prefix = self.options.total_prefix
                total[k] = stor
        return total

    @property
    def percent(self):
        """ Disk percent property """
        perc = None
        if self.original_dev is not None:
            perc = dict()
            used = self.used
            total = self.total
            for dev in self.original_dev.keys():
                value = percent(used[dev].value, total[dev].value)
                if value is None:
                    value = 0.0
                else:
                    value = _round(value, self.options.percent_round)
                perc[dev] = value
        return perc


class AbstractBattery(AbstractGetter):
    """ Abstract battery class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["is_present", "is_charging", "is_full", "percent",
                "time", "power"]

    @property
    @abstractmethod
    def is_present(self):
        """ Abstract battery present method to be implemented by subclass """

    @property
    @abstractmethod
    def is_charging(self):
        """ Abstract battery charging method to be implemented by subclass """

    @property
    @abstractmethod
    def is_full(self):
        """ Abstract battery full method to be implemented by subclass """

    @property
    @abstractmethod
    def percent(self):
        """ Abstract battery percent method to be implemented by subclass """

    @property
    @abstractmethod
    def _time(self):
        """
        Abstract battery time remaining method to be implemented by subclass
        """

    @property
    def time(self):
        """ Battery time method """
        return unix_epoch_to_str(self._time)

    @property
    @abstractmethod
    def power(self):
        """
        Abstract battery power usage method to be implemented by subclass
        """


class AbstractNetwork(AbstractGetter):
    """ Abstract network class to be implemented by subclass """

    @property
    def _valid_info(self):
        return ["dev", "ssid", "local_ip", "download", "upload"]

    @property
    @abstractmethod
    def _LOCAL_IP_CMD(self):
        pass

    @property
    @lru_cache(maxsize=1)
    @abstractmethod
    def dev(self):
        """ Abstract network device method to be implemented by subclass """

    @property
    @abstractmethod
    def _ssid(self):
        """ Abstract ssid resource method to be implemented by subclass """

    @property
    def ssid(self):
        """ Network ssid method """
        ssid = None
        cmd, reg = self._ssid
        if not (cmd is None or reg is None):
            ssid = (reg.match(i.strip()) for i in run(cmd).split("\n"))
            ssid = next((i.group(1) for i in ssid if i), None)

        return ssid

    @property
    def local_ip(self):
        """ Network local ip method """
        ip_out = None
        if self.dev is not None:
            reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
            ip_out = run(self._LOCAL_IP_CMD + [self.dev]).strip().split("\n")
            ip_out = (reg.match(line.strip()) for line in ip_out)
            ip_out = next((i.group(1) for i in ip_out if i), None)
        return ip_out

    @abstractmethod
    def _bytes_delta(self, dev, mode):
        """
        Abstract network bytes delta method to fetch the change in bytes on
        a device depending on mode
        """

    def _bytes_rate(self, mode):
        """
        Abstract network bytes rate method to fetch the rate of change in bytes
        on a device depending on mode
        """
        if self.dev is None:
            return 0.0

        start = self._bytes_delta(self.dev, mode)
        start_time = time.time()

        # Timeout after 2 seconds
        while (self._bytes_delta(self.dev, mode) <= start and
               time.time() - start_time < 2):
            pass

        end = self._bytes_delta(self.dev, mode)
        if end == start:
            return 0.0

        end_time = time.time()
        delta_bytes = end - start
        delta_time = end_time - start_time

        return delta_bytes / delta_time

    @property
    def download(self):
        """ Network download method """
        download = Storage(value=self._bytes_rate("down"),
                           rounding=self.options.download_round)
        download.prefix = self.options.download_prefix
        return download

    @property
    def upload(self):
        """ Network upload method """
        upload = Storage(value=self._bytes_rate("up"),
                         rounding=self.options.upload_round)
        upload.prefix = self.options.upload_prefix
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

    @property
    def _valid_info(self):
        return ["date", "time"]

    @property
    def now(self):
        """ Return current date and time """
        return datetime.now()

    def _format(self, fmt):
        """ Wrapper for printing date and time format """
        return "{{:{}}}".format(fmt).format(self.now)

    @property
    def date(self):
        """ Returns the date as a string from a specified format """
        return self._format(self.options.date_format)

    @property
    def time(self):
        """ Returns the time as a string from a specified format """
        return self._format(self.options.time_format)


class AbstractMisc(AbstractGetter):
    """ Misc class for fetching miscellaneous information """

    @property
    def _valid_info(self):
        return ["vol", "scr"]

    @property
    @abstractmethod
    def vol(self):
        """ Abstract volume method to be implemented by subclass """

    @property
    @abstractmethod
    def scr(self):
        """ Abstract screen brightness method to be implemented by subclass """


class System(ABC):
    """
    Abstract System class to store all the assigned getters from the sub class
    that implements this class
    """

    DOMAINS = ("cpu", "memory", "swap", "disk",
               "battery", "network", "date", "misc")
    SHORT_DOMAINS = ("cpu", "mem", "swap", "disk",
                     "bat", "net", "date", "misc")

    def __init__(self, options, aux = None, cpu = None, mem = None,
                 swap = None, disk = None, bat = None, net = None,
                 misc = None):
        super(System, self).__init__()

        self.options = options
        self.aux = aux

        self._getters = {
            "cpu": cpu, "mem": mem, "swap": swap, "disk": disk,
            "bat": bat, "net": net, "date": Date, "misc": misc
        }

    @property
    @lru_cache(maxsize=1)
    def cpu(self):
        """ Return an instance of AbstractCpu """
        return self._getters["cpu"]("cpu", self.options.cpu, self.aux)

    @property
    @lru_cache(maxsize=1)
    def mem(self):
        """ Return an instance of AbstractMemory """
        return self._getters["mem"]("mem", self.options.mem, self.aux)

    @property
    @lru_cache(maxsize=1)
    def swap(self):
        """ Return an instance of AbstractSwap """
        return self._getters["swap"]("swap", self.options.swap, self.aux)

    @property
    @lru_cache(maxsize=1)
    def disk(self):
        """ Return an instance of AbstractDisk """
        return self._getters["disk"]("disk", self.options.disk, self.aux)

    @property
    @lru_cache(maxsize=1)
    def bat(self):
        """ Return an instance of AbstractBattery """
        return self._getters["bat"]("bat", self.options.bat, self.aux)

    @property
    @lru_cache(maxsize=1)
    def net(self):
        """ Return an instance of AbstractNetwork """
        return self._getters["net"]("net", self.options.net, self.aux)

    @property
    @lru_cache(maxsize=1)
    def date(self):
        """ Return an instance of Date """
        return self._getters["date"]("date", self.options.date, self.aux)

    @property
    @lru_cache(maxsize=1)
    def misc(self):
        """ Return an instance of AbstractMisc """
        return self._getters["misc"]("misc", self.options.misc, self.aux)
