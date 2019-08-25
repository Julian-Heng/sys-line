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
from argparse import Namespace
from datetime import datetime
from functools import lru_cache
from sys import version_info
from types import SimpleNamespace
from typing import List

from ..tools.storage import Storage
from ..tools.utils import percent, run, unix_epoch_to_str, _round


""" Python 3.6 and lower does not have re.Pattern class """
if version_info[0] == 3 and version_info[1] <= 6:
    RE_COMPILE = type(re.compile(""))
else:
    RE_COMPILE = re.Pattern


class AbstractGetter(ABC):
    """
    Abstract Getter class to store both options and any auxilary classes
    """

    def __init__(self,
                 domain_name: str,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(AbstractGetter, self).__init__()

        self.domain_name = domain_name
        self.options = options
        self.aux = aux


    def __str__(self) -> str:
        """ The string representation of the getter would return all values """
        return "\n".join([
            "{}.{}: {}".format(self.domain_name, i, getattr(self, i))
            for i in self.__info
        ])


    @property
    @abstractmethod
    def __info(self) -> List[str]:
        """ Returns list of info in getter """


class System(ABC):
    """
    Abstract System class to store all the assigned getters from the sub class
    that implements this class
    """

    DOMAINS = ("cpu", "memory", "swap", "disk",
               "battery", "network", "date", "misc")
    SHORT_DOMAINS = ("cpu", "mem", "swap", "disk",
                     "bat", "net", "date", "misc")

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None,
                 cpu: AbstractGetter = None,
                 mem: AbstractGetter = None,
                 swap: AbstractGetter = None,
                 disk: AbstractGetter = None,
                 bat: AbstractGetter = None,
                 net: AbstractGetter = None,
                 misc: AbstractGetter = None) -> None:
        super(System, self).__init__()

        self.options = options
        self.aux = aux

        self.__getters = {
            "cpu": cpu,
            "mem": mem,
            "swap": swap,
            "disk": disk,
            "bat": bat,
            "net": net,
            "date": Date,
            "misc": misc
        }


    @property
    @lru_cache(maxsize=1)
    def cpu(self) -> AbstractGetter:
        """ Return an instance of AbstractCpu """
        return self.__getters["cpu"]("cpu", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def mem(self) -> AbstractGetter:
        """ Return an instance of AbstractMemory """
        return self.__getters["mem"]("mem", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def swap(self) -> AbstractGetter:
        """ Return an instance of AbstractSwap """
        return self.__getters["swap"]("swap", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def disk(self) -> AbstractGetter:
        """ Return an instance of AbstractDisk """
        return self.__getters["disk"]("disk", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def bat(self) -> AbstractGetter:
        """ Return an instance of AbstractBattery """
        return self.__getters["bat"]("bat", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def net(self) -> AbstractGetter:
        """ Return an instance of AbstractNetwork """
        return self.__getters["net"]("net", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def date(self) -> AbstractGetter:
        """ Return an instance of Date """
        return self.__getters["date"]("date", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def misc(self) -> AbstractGetter:
        """ Return an instance of AbstractMisc """
        return self.__getters["misc"]("misc", self.options, self.aux)


class AbstractStorage(AbstractGetter):
    """
    AbstractStorage for info that fetches used, total and percent attributes
    """

    def __init__(self,
                 domain_name: str,
                 options: Namespace,
                 aux: SimpleNamespace,
                 rounding: int = 2) -> None:
        super(AbstractStorage, self).__init__(domain_name, options, aux=aux)
        self.rounding = rounding


    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["used", "total", "percent"]


    @property
    @abstractmethod
    def used(self) -> Storage:
        """ Abstract used property to be implemented by subclass """


    @property
    @abstractmethod
    def total(self) -> Storage:
        """ Abstract total property to be implemented by subclass """


    @property
    def percent(self) -> [float, int]:
        """ Abstract percent property """
        perc = percent(self.used, self.total)
        if perc is not None:
            perc = perc.value if isinstance(perc, Storage) else perc
            perc = _round(perc, self.rounding)

        return perc


class AbstractCpu(AbstractGetter):
    """ Abstract cpu class to be implemented by subclass """

    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["cores", "cpu", "load_avg",
                "cpu_usage", "fan", "temp", "uptime"]


    @property
    @abstractmethod
    def cores(self) -> int:
        """ Abstract cores method to be implemented by subclass """


    @abstractmethod
    def __cpu_speed(self) -> (str, [float, int]):
        """
        Private abstract cpu and speed method to be implemented by subclass
        """


    @property
    def cpu(self) -> str:
        """ Returns cpu string """
        cpu_reg = re.compile(r"\s+@\s+(\d+\.)?\d+GHz")
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        cores = self.cores
        cpu, speed = self.__cpu_speed()
        cpu = trim_reg.sub("", cpu.strip())

        if speed is not None:
            fmt = r" ({}) @ {}GHz".format(cores, speed)
            cpu = cpu_reg.sub(fmt, cpu)
        else:
            fmt = r"({}) @".format(cores)
            cpu = re.sub(r"@", fmt, cpu)

        cpu = re.sub(r"\s+", " ", cpu)

        return cpu


    @property
    @abstractmethod
    def load_avg(self) -> str:
        """ Abstract load average method to be implemented by subclass """


    @property
    def cpu_usage(self) -> [float, int]:
        """ Cpu usage method """
        cores = self.cores
        ps_out = run(["ps", "-e", "-o", "%cpu"]).strip().split("\n")[1:]
        cpu_usage = sum([float(i) for i in ps_out]) / cores
        return _round(cpu_usage, self.options.cpu_usage_round)


    @property
    @abstractmethod
    def fan(self) -> int:
        """ Abstract fan method to be implemented by subclass """


    @property
    @abstractmethod
    def temp(self) -> [float, int]:
        """ Abstract temperature method to be implemented by subclass """


    @abstractmethod
    def __uptime(self):
        """ Abstract uptime method to be implemented by subclass """


    @property
    def uptime(self) -> str:
        """ Uptime method """
        return unix_epoch_to_str(self.__uptime())


class AbstractMemory(AbstractStorage):
    """ Abstract memory class to be implemented by subclass """

    @property
    @abstractmethod
    def used(self) -> Storage:
        pass


    @property
    @abstractmethod
    def total(self) -> Storage:
        pass


class AbstractSwap(AbstractStorage):
    """ Abstract swap class to be implemented by subclass """

    @property
    @abstractmethod
    def used(self) -> Storage:
        pass


    @property
    @abstractmethod
    def total(self) -> Storage:
        pass


class AbstractDisk(AbstractStorage):
    """ Abstract disk class to be implemented by subclass """

    def __str__(self) -> str:
        return "{}\n{}".format("\n".join([
            "{}.{}: {}".format(self.domain_name, i, getattr(self, i))
            for i in self.__info
        ]), super(AbstractDisk, self).__str__())


    @property
    def __info(self) -> List[str]:
        return ["dev", "mount", "name", "partition"]


    @property
    @lru_cache(maxsize=1)
    def df_out(self):
        """ Return df output """
        df_out = None
        df_flags = self.DF_FLAGS

        if self.options.disk is None:
            df_flags.append(self.options.mount)

        df_out = run(df_flags)
        return df_out.strip().split("\n")[1].split() if df_out else None


    @property
    def dev(self):
        """ Disk device method """
        dev = None
        df_out = self.df_out
        if df_out is not None:
            dev = df_out[0]
            if self.options.disk_short_dev:
                dev = dev.split("/")[-1]
        return dev


    @property
    @abstractmethod
    def name(self) -> str:
        """ Abstract disk name method to be implemented by subclass """


    @property
    def mount(self) -> str:
        """ Abstract disk mount method to be implemented by subclass """
        return self.df_out[5] if self.df_out else None


    @property
    @abstractmethod
    def partition(self) -> str:
        """ Abstract disk partition method to be implemented by subclass """


    @property
    def used(self) -> Storage:
        """ Abstract disk used method to be implemented by subclass """
        used = None
        if self.df_out is not None and self.dev is not None:
            used = Storage(value=int(self.df_out[2]), prefix="KiB",
                           rounding=self.options.disk_used_round)
            used.prefix = self.options.disk_used_prefix
        return used


    @property
    def total(self) -> Storage:
        """ Abstract disk total method to be implemented by subclass """
        total = None
        if self.df_out is not None and self.dev is not None:
            total = Storage(value=int(self.df_out[1]), prefix="KiB",
                            rounding=self.options.disk_total_round)
            total.prefix = self.options.disk_total_prefix
        return total


class AbstractBattery(AbstractGetter):
    """ Abstract battery class to be implemented by subclass """

    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["is_present", "is_charging", "is_full", "percent",
                "time", "power"]


    @property
    @abstractmethod
    def is_present(self) -> bool:
        """ Abstract battery present method to be implemented by subclass """


    @property
    @abstractmethod
    def is_charging(self) -> bool:
        """ Abstract battery charging method to be implemented by subclass """


    @property
    @abstractmethod
    def is_full(self) -> bool:
        """ Abstract battery full method to be implemented by subclass """


    @property
    @abstractmethod
    def percent(self) -> bool:
        """ Abstract battery percent method to be implemented by subclass """


    @property
    @abstractmethod
    def __time(self) -> int:
        """
        Abstract battery time remaining method to be implemented by subclass
        """


    @property
    def time(self) -> str:
        """ Battery time method """
        return unix_epoch_to_str(self.__time)


    @property
    @abstractmethod
    def power(self) -> bool:
        """
        Abstract battery power usage method to be implemented by subclass
        """


class AbstractNetwork(AbstractGetter):
    """ Abstract network class to be implemented by subclass """

    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["dev", "ssid", "local_ip", "download", "upload"]


    @property
    @lru_cache(maxsize=1)
    @abstractmethod
    def dev(self) -> str:
        """ Abstract network device method to be implemented by subclass """


    @property
    @abstractmethod
    def __ssid(self) -> (List[str], RE_COMPILE):
        """ Abstract ssid resource method to be implemented by subclass """


    @property
    def ssid(self) -> str:
        """ Network ssid method """
        ssid = None
        cmd, reg = self.__ssid
        if not (cmd is None or reg is None):
            ssid = (reg.match(i.strip()) for i in run(cmd).split("\n"))
            ssid = next((i.group(1) for i in ssid if i), None)

        return ssid


    @property
    def local_ip(self) -> str:
        """ Network local ip method """
        if self.dev is None:
            return None

        reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
        ip_out = run(self.LOCAL_IP_CMD + [self.dev]).strip().split("\n")
        ip_out = (reg.match(line.strip()) for line in ip_out)
        return next((i.group(1) for i in ip_out if i), None)


    @abstractmethod
    def __bytes_delta(self, dev: str, mode: str) -> int:
        """
        Abstract network bytes delta method to fetch the change in bytes on
        a device depending on mode
        """


    def __bytes_rate(self, mode: str) -> float:
        """
        Abstract network bytes rate method to fetch the rate of change in bytes
        on a device depending on mode
        """
        if self.dev is None:
            return 0.0

        start = self.__bytes_delta(self.dev, mode)
        start_time = time.time()

        # Timeout after 2 seconds
        while (self.__bytes_delta(self.dev, mode) <= start and
               time.time() - start_time < 2):
            pass

        end = self.__bytes_delta(self.dev, mode)
        if end == start:
            return 0.0

        end_time = time.time()
        delta_bytes = end - start
        delta_time = end_time - start_time

        return delta_bytes / delta_time


    @property
    def download(self) -> Storage:
        """ Network download method """
        download = Storage(value=self.__bytes_rate("down"),
                           rounding=self.options.net_download_round)
        download.prefix = self.options.net_download_prefix
        return download


    @property
    def upload(self) -> Storage:
        """ Network upload method """
        upload = Storage(value=self.__bytes_rate("up"),
                         rounding=self.options.net_upload_round)
        upload.prefix = self.options.net_upload_prefix
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["date", "time"]


    @property
    def now(self) -> datetime:
        """ Return current date and time """
        return datetime.now()


    def __format(self, fmt: str) -> str:
        """ Wrapper for printing date and time format """
        return "{{:{}}}".format(fmt).format(self.now)


    @property
    def date(self) -> str:
        """ Returns the date as a string from a specified format """
        return self.__format(self.options.date_format)


    @property
    def time(self) -> str:
        """ Returns the time as a string from a specified format """
        return self.__format(self.options.time_format)


class AbstractMisc(AbstractGetter):
    """ Misc class for fetching miscellaneous information """

    @property
    def _AbstractGetter__info(self) -> List[str]:
        return ["vol", "scr"]


    @property
    @abstractmethod
    def vol(self) -> [float, int]:
        """ Abstract volume method to be implemented by subclass """


    @property
    @abstractmethod
    def scr(self) -> [float, int]:
        """ Abstract screen brightness method to be implemented by subclass """
