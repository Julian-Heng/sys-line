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
from typing import Any, Generator, List, Match, Optional, Pattern, Tuple, Union

from ..tools.storage import Storage
from ..tools.utils import percent, run, unix_epoch_to_str, _round


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
    def percent(self) -> Union[float, int]:
        """ Abstract percent property """
        perc = percent(self.used.value, self.total.value)
        perc = 0.0 if perc is None else _round(perc, self.rounding)
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
    def __cpu_speed(self) -> Tuple[str, Union[float, int]]:
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
    def cpu_usage(self) -> Union[float, int]:
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
    def temp(self) -> Union[float, int]:
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
    def df_out(self) -> str:
        """ Return df output """
        df_output = None
        df_lines = None
        df_cmd = self.DF_FLAGS

        if self.options.disk is None:
            df_cmd += self.options.mount
        else:
            df_cmd += self.options.disk

        df_output = run(df_cmd).strip().split("\n")

        if (len(df_output) <= 1):
            df_output = run(df_cmd[:-1]).split("\n")

        if len(df_output) == 2:
            df_lines = [df_output[1].split()]
        else:
            if self.options.disk is not None:
                reg = re.compile("|".join(self.options.disk))
            else:
                reg = re.compile("({})$".format("|".join(self.options.mount)))

            find_dev = (i.split() for i in df_output if i and reg.search(i))
            fallback = (i.split() for i in df_output if i.endswith("/"))

            df_lines = list(find_dev)
            if len(df_lines) == 0:
                df_lines = next(fallback, None)

        return df_lines


    @property
    def original_dev(self):
        """ Disk device without modification """
        dev = None
        df_out = self.df_out
        if df_out is not None:
            dev = [i[0] for i in df_out]
        return dev


    @property
    def dev(self):
        """ Disk device method """
        dev = self.original_dev
        if self.options.disk_short_dev:
            dev = [i.split("/")[-1] for i in dev]
        return dev


    @property
    @abstractmethod
    def name(self) -> str:
        """ Abstract disk name method to be implemented by subclass """


    @property
    def mount(self) -> str:
        """ Abstract disk mount method to be implemented by subclass """
        return [i[5] for i in self.df_out] if self.df_out is not None else None


    @property
    @abstractmethod
    def partition(self) -> str:
        """ Abstract disk partition method to be implemented by subclass """


    @property
    def used(self) -> Storage:
        """ Abstract disk used method to be implemented by subclass """
        used = list()
        if self.df_out is not None:
            for i in self.df_out:
                stor = Storage(value=int(i[2]), prefix="KiB",
                               rounding=self.options.disk_used_round)
                stor.prefix = self.options.disk_used_prefix
                used.append(stor)
        return used


    @property
    def total(self) -> Storage:
        """ Abstract disk total method to be implemented by subclass """
        total = list()
        if self.df_out is not None:
            for i in self.df_out:
                stor = Storage(value=int(i[1]), prefix="KiB",
                                rounding=self.options.disk_total_round)
                stor.prefix = self.options.disk_total_prefix
                total.append(stor)
        return total


    @property
    def percent(self) -> Union[float, int]:
        """ Abstract percent property """
        perc = list()
        for used, total in zip(self.used, self.total):
            value = percent(used.value, total.value)
            value = 0.0 if value is None else _round(value, self.rounding)
            perc.append(value)
        return perc


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
    def __ssid(self) -> Tuple[List[str], Pattern]:
        """ Abstract ssid resource method to be implemented by subclass """


    @property
    def ssid(self) -> Optional[Generator[Optional[Match[Any]], None, None]]:
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
        ip_out = None
        if self.dev is not None:
            reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
            ip_out = run(self.LOCAL_IP_CMD + [self.dev]).strip().split("\n")
            ip_out = (reg.match(line.strip()) for line in ip_out)
            ip_out = next((i.group(1) for i in ip_out if i), None)
        return ip_out


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
    def vol(self) -> Union[float, int]:
        """ Abstract volume method to be implemented by subclass """


    @property
    @abstractmethod
    def scr(self) -> Union[float, int]:
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
    def cpu(self) -> AbstractCpu:
        """ Return an instance of AbstractCpu """
        return self.__getters["cpu"]("cpu", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def mem(self) -> AbstractMemory:
        """ Return an instance of AbstractMemory """
        return self.__getters["mem"]("mem", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def swap(self) -> AbstractSwap:
        """ Return an instance of AbstractSwap """
        return self.__getters["swap"]("swap", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def disk(self) -> AbstractDisk:
        """ Return an instance of AbstractDisk """
        return self.__getters["disk"]("disk", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def bat(self) -> AbstractBattery:
        """ Return an instance of AbstractBattery """
        return self.__getters["bat"]("bat", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def net(self) -> AbstractNetwork:
        """ Return an instance of AbstractNetwork """
        return self.__getters["net"]("net", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def date(self) -> Date:
        """ Return an instance of Date """
        return self.__getters["date"]("date", self.options, self.aux)


    @property
    @lru_cache(maxsize=1)
    def misc(self) -> AbstractMisc:
        """ Return an instance of AbstractMisc """
        return self.__getters["misc"]("misc", self.options, self.aux)
