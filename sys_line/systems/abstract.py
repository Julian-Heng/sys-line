#!/usr/bin/env python3
# pylint: disable=no-member,invalid-name,no-self-use,pointless-string-statement

""" Abstract classes for getting system info """

import re
import sys
import time

from abc import ABCMeta, abstractmethod
from argparse import Namespace
from datetime import datetime
from types import SimpleNamespace
from typing import Dict, List

from ..tools.storage import Storage
from ..tools.utils import percent, run, unix_epoch_to_str, _round


""" Python 3.6 and lower does not have re.Pattern class """
if sys.version_info[0] == 3 and sys.version_info[1] <= 6:
    RE_COMPILE = type(re.compile(""))
else:
    RE_COMPILE = re.Pattern


class AbstractGetter(metaclass=ABCMeta):
    """ Abstract class to map the available functions to names """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(AbstractGetter, self).__init__()
        check = lambda i: i != "get" and i.startswith("get")
        extract = lambda i: i.split("_", 1)[1]

        # Find all "get_*" methods in the child class and maps them to
        #    1. A map called info to store fetched values into
        #    2. A map called func to store the function to get the value
        self.info = {extract(i): None for i in dir(self) if check(i)}
        self.func = {i: getattr(self, "get_{}".format(i)) for i in self.info}
        self.options = options
        self.aux = aux


    def call(self, name: str) -> None:
        """ Fetch the info """
        try:
            self.info[name] = self.func[name]()
        except KeyError:
            pass


    def get(self, name: str) -> object:
        """ Return the value """
        try:
            return self.info[name]
        except KeyError:
            return None


    def call_get(self, name: str) -> object:
        """ Wrapper for retuning info that has not been called yet """
        ret = None
        try:
            if self.info[name] is None:
                self.info[name] = self.func[name]()
            ret = self.info[name]
        except KeyError:
            pass
        return ret


    def return_all(self) -> (str, object):
        """ Return all available info in this getter """
        for k, v in self.func.items():
            try:
                yield (k, v())
            except NotImplementedError:
                yield (k, None)


class System(metaclass=ABCMeta):
    """ Abstract system class for mapping functions """

    def __init__(self,
                 domains: Dict[str, AbstractGetter],
                 os_name: str,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(System, self).__init__()

        self.domains = domains
        self.domains["date"] = Date

        # Create a map of domains to determine if it's loaded
        self.loaded = dict.fromkeys(self.domains.keys(), False)
        self.os_name = os_name
        self.options = options
        self.aux = aux


    def fetch(self, domain: Dict[str, AbstractGetter], info: str) -> None:
        """ Fetch the info from the system """
        if not self.loaded[domain]:
            self.domains[domain] = self.domains[domain](self.options,
                                                        aux=self.aux)
            self.loaded[domain] = True

        try:
            self.domains[domain].call(info)
        except NotImplementedError:
            pass


    def get(self, domain: Dict[str, AbstractGetter], info: str) -> object:
        """ Return the requested value """
        return self.domains[domain].get(info)


    def return_all(self, domains: List[str] = None) -> (str, object):
        """ Return all available info from domains """
        for domain in domains if domains else self.domains.keys():
            if not self.loaded[domain]:
                self.domains[domain] = self.domains[domain](self.options,
                                                            aux=self.aux)
                self.loaded[domain] = True
            for k, v in self.domains[domain].return_all():
                yield ("{}.{}".format(domain, k), v)


class AbstractStorage(AbstractGetter):
    """
    Abstract class for info that has a get_used, get_total and get_percent
    methods
    """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None,
                 rounding: int = 2) -> None:
        super(AbstractStorage, self).__init__(options, aux=aux)
        self.rounding = rounding


    @abstractmethod
    def get_used(self) -> Storage:
        """
        Abstract used method to be implemented by subclass
        Returns Storage class
        """


    @abstractmethod
    def get_total(self) -> Storage:
        """
        Abstract total method to be implemented by subclass
        Returns Storage class
        """


    def get_percent(self) -> [float, int]:
        """ Returns percentage in the same object type as the values used """
        perc = percent(self.call_get("used"), self.call_get("total"))
        if perc is not None:
            perc = perc.value if isinstance(perc, Storage) else perc
            perc = _round(perc, self.rounding)

        return perc


class AbstractCpu(AbstractGetter):
    """ Abstract cpu class """

    @abstractmethod
    def get_cores(self) -> int:
        """
        Abstract cores method to be implemented
        Returns the number of cpu cores as an int
        """


    @abstractmethod
    def _get_cpu_speed(self) -> (str, [float, int]):
        """
        Abstract cpu method to be implemented
        Returns the cpu and the cpu speed
        """


    def get_cpu(self) -> str:
        """ Returns cpu string """
        cpu_reg = re.compile(r"\s+@\s+(\d+\.)?\d+GHz")
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        cores = self.call_get("cores")
        cpu, speed = self._get_cpu_speed()
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
    def get_load_avg(self) -> str:
        """
        Abstract load method to be implemented
        Returns load average as a string
        """


    def get_cpu_usage(self) -> [float, int]:
        """ Returns the cpu usage in the system """
        cores = self.call_get("cores")
        ps_out = run(["ps", "-e", "-o", "%cpu"]).strip().split("\n")[1:]
        cpu_usage = sum([float(i) for i in ps_out]) / cores
        return _round(cpu_usage, self.options.cpu_usage_round)


    @abstractmethod
    def get_fan(self) -> int:
        """
        Abstract fan method to be implemented
        Returns the fan speed as an int
        """


    @abstractmethod
    def get_temp(self) -> float:
        """
        Abstract temp method to be implemented
        Returns the cpu temperature as a float
        """


    @abstractmethod
    def _get_uptime_sec(self) -> int:
        """
        Abstract uptime method to be implemented
        Returns the system uptime in seconds
        """


    def get_uptime(self) -> str:
        """ Formats system uptime """
        return unix_epoch_to_str(self._get_uptime_sec())


class AbstractMemory(AbstractStorage):
    """ Abstract memory class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(AbstractMemory, self).__init__(options,
                                             aux,
                                             options.mem_percent_round)


    @abstractmethod
    def get_used(self) -> Storage:
        pass


    @abstractmethod
    def get_total(self) -> Storage:
        pass


class AbstractSwap(AbstractStorage):
    """ Abstract swap class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(AbstractSwap, self).__init__(options,
                                           aux=aux,
                                           rounding=options.swap_percent_round)


    @abstractmethod
    def get_used(self) -> Storage:
        pass


    @abstractmethod
    def get_total(self) -> Storage:
        pass


class AbstractDisk(AbstractStorage):
    """ Abstract disk class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(AbstractDisk, self).__init__(options,
                                           aux=aux,
                                           rounding=options.disk_percent_round)
        self.df_out = None


    def get_dev(self) -> str:
        """ Returns the device name of the disk """
        dev = None

        if self.options.disk is not None:
            reg = r"^({})".format(self.options.disk)
        else:
            self.df_flags.append(self.options.mount)
            reg = r"^([^\s]+)(\s+\d+%?){{4}}\s+({})$".format(self.options.mount)

        self.df_out = run(self.df_flags).strip().split("\n")[1:]
        match = ((re.match(reg, line), line) for line in self.df_out)

        entry = next((i for i in match if i[0]), None)
        if entry is not None:
            dev = entry[0].group(1)
            self.df_out = entry[1].split(maxsplit=6)
            if self.options.disk_short_dev:
                dev = dev.split("/")[-1]
        else:
            self.df_out = None

        return dev


    @abstractmethod
    def get_name(self) -> str:
        """
        Abstract disk name method to be implemented
        Returns the name of the disk as a string
        """


    def get_mount(self):
        """ Returns the mount point of the disk as a string """
        if self.df_out is None or self.get("dev") is None:
            self.call("dev")
        return self.df_out[5] if self.df_out else None


    @abstractmethod
    def get_partition(self) -> str:
        """
        Abstract disk partition method to be implemented
        Returns the partition type of the disk as a string
        """


    def get_used(self) -> Storage:
        """
        Abstract disk used method to be implemented
        Returns system used disk as a Storage class
        """
        self.call_get("dev")
        used = Storage(value=int(self.df_out[2]), prefix="KiB",
                       rounding=self.options.disk_used_round)
        used.prefix = self.options.disk_used_prefix
        return used


    def get_total(self) -> Storage:
        """
        Abstract disk total method to be implemented
        Returns system total disk as a Storage class
        """
        self.call_get("dev")
        total = Storage(value=int(self.df_out[1]), prefix="KiB",
                        rounding=self.options.disk_total_round)
        total.prefix = self.options.disk_total_prefix
        return total


class AbstractBattery(AbstractGetter):
    """ Abstract battery class """

    @abstractmethod
    def get_is_present(self) -> bool:
        """
        Abstract method to determine if the system has a battery installed
        Returns a bool
        """


    @abstractmethod
    def get_is_charging(self) -> bool:
        """
        Abstract method to determine if the battery is charging
        Returns a bool
        """


    @abstractmethod
    def get_is_full(self) -> bool:
        """
        Abstract method to determine if the battery is full
        Returns a bool
        """


    @abstractmethod
    def get_percent(self) -> [float, int]:
        """
        Abstract method to calculate the battery percentage
        Returns a float
        """


    @abstractmethod
    def _get_time(self) -> int:
        """
        Abstract method to calculate battery time remaining
        Returns an int
        """


    def get_time(self) -> str:
        """ Formats battery time remaining """
        secs = self._get_time()
        secs = unix_epoch_to_str(secs) if secs else None
        return secs


    @abstractmethod
    def get_power(self) -> [float, int]:
        """
        Abstract method to calculate system power usage
        Returns a float
        """


class AbstractNetwork(AbstractGetter):
    """ Abstract network class """

    @abstractmethod
    def get_dev(self) -> str:
        """
        Abstract network device method to be implemented
        Returns a string
        """


    @abstractmethod
    def _get_ssid(self) -> (List[str], RE_COMPILE):
        """
        Abstract network ssid method to be implemented
        """


    def get_ssid(self) -> str:
        """ Returns the network ssid as a string """
        ssid = None
        cmd, reg = self._get_ssid()
        if not (cmd is None or reg is None):
            ssid = (reg.match(i.strip()) for i in run(cmd).split("\n"))
            ssid = next((i.group(1) for i in ssid if i), None)

        return ssid


    def get_local_ip(self) -> str:
        """ Returns the network local ip as a string """
        dev = self.call_get("dev")
        if dev is None:
            return None

        reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
        ip_out = run(self.local_ip_cmd + [dev]).strip().split("\n")
        ip_out = (reg.match(line.strip()) for line in ip_out)
        return next((i.group(1) for i in ip_out if i), None)


    @abstractmethod
    def _get_bytes_delta(self, dev: str, mode: str) -> int:
        """
        Abstract method to fetch change in bytes
        dev determines the device to check
        mode determines which delta bytes to find
        Returns an int
        """


    def __calc_bytes_delta_rate(self, mode: str) -> float:
        """
        Private method to calculate the rate of change in bytes
        Returns a float
        """
        dev = self.call_get("dev")
        if dev is None:
            return 0.0

        start = self._get_bytes_delta(dev, mode)
        start_time = time.time()

        # Timeout after 2 seconds
        while (self._get_bytes_delta(dev, mode) <= start and
               time.time() - start_time < 2):
            pass

        end = self._get_bytes_delta(dev, mode)
        if end == start:
            return 0.0

        end_time = time.time()
        delta_bytes = end - start
        delta_time = end_time - start_time

        return delta_bytes / delta_time


    def get_download(self) -> Storage:
        """
        Method to calculate network download speed
        Returns a Storage class
        """
        download = Storage(value=self.__calc_bytes_delta_rate("down"),
                           rounding=self.options.net_download_round)
        download.prefix = self.options.net_download_prefix
        return download


    def get_upload(self) -> Storage:
        """
        Method to calculate network upload speed
        Returns a Storage class
        """
        upload = Storage(value=self.__calc_bytes_delta_rate("up"),
                         rounding=self.options.net_upload_round)
        upload.prefix = self.options.net_upload_prefix
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Date, self).__init__(options, aux=aux)
        self.now = datetime.now()


    def __format(self, fmt: str) -> str:
        """ Wrapper for printing date and time format """
        fmt = "{{:{}}}".format(fmt)
        return fmt.format(self.now)


    def get_date(self) -> str:
        """ Returns the date as a string from a specified format """
        return self.__format(self.options.date_format)


    def get_time(self) -> str:
        """ Returns the time as a string from a specified format """
        return self.__format(self.options.time_format)


class AbstractMisc(AbstractGetter):
    """ Misc class for fetching miscellaneous information """

    @abstractmethod
    def get_vol(self) -> [float, int]:
        """
        Abstract volume method to be implemented
        Returns a float
        """


    @abstractmethod
    def get_scr(self) -> [float, int]:
        """
        Abstract screen brightness method to be implemented
        Returns a float
        """
