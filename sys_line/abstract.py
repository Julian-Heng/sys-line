#!/usr/bin/env python3
# pylint: disable=no-member

""" Abstract classes for getting system info """

import re
import time

from abc import ABCMeta, abstractmethod
from datetime import datetime

from .storage import Storage
from .utils import percent, run, unix_epoch_to_str


class System(metaclass=ABCMeta):
    """ Abstract system class for mapping functions """

    def __init__(self, domains, os_name, options):
        self.domains = domains
        self.domains["date"] = Date

        # Create a map of domains to determine if it's loaded
        self.loaded = dict.fromkeys(self.domains.keys(), False)
        self.os_name = os_name
        self.options = options

        super().__init__()


    def fetch(self, domain, info):
        """ Fetch the info from the system """
        if not self.loaded[domain]:
            self.domains[domain] = self.domains[domain](self.options)
            self.loaded[domain] = True
        self.domains[domain].call(info)


    def get(self, domain, info):
        """ Return the requested value """
        return self.domains[domain].get(info)


class AbstractGetter(metaclass=ABCMeta):
    """ Abstract class to map the available functions to names """

    def __init__(self, options):
        super().__init__()
        check = lambda i: i != "get" and i.startswith("get")
        extract = lambda i: i.split("_", 1)[1]

        # Find all "get_*" methods in the child class and maps them to
        #    1. A map called info to store fetched values into
        #    2. A map called func to store the function to get the value
        self.info = {extract(i): None for i in dir(self) if check(i)}
        self.func = {extract(i): getattr(self, i) for i in dir(self) if check(i)}
        self.options = options


    def call(self, name):
        """ Fetch the info """
        try:
            self.info[name] = self.func[name]()
        except KeyError:
            pass


    def get(self, name):
        """ Return the value """
        try:
            return self.info[name]
        except KeyError:
            return None


class AbstractCpu(AbstractGetter):
    """ Abstract cpu class """

    @abstractmethod
    def get_cores(self):
        """
        Abstract cores method to be implemented
        Returns the number of cpu cores as an int
        """


    @abstractmethod
    def _get_cpu_speed(self):
        """
        Abstract cpu method to be implemented
        Returns the cpu and the cpu speed
        """


    def get_cpu(self):
        """ Returns cpu string """
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        if self.get("cores") is None:
            self.call("cores")

        cpu, speed = self._get_cpu_speed()
        cpu = trim_reg.sub("", cpu.strip())

        if speed is not None:
            fmt = r" ({}) @ {}GHz"
            fmt = fmt.format(self.get("cores"), speed)
        else:
            fmt = r"({}) @"
            fmt = fmt.format(self.get("cores"))

        cpu = re.sub(r"@", fmt, cpu)
        cpu = re.sub(r"\s+", " ", cpu)

        return cpu


    @abstractmethod
    def get_load_avg(self):
        """
        Abstract load method to be implemented
        Returns load average as a string
        """


    def get_cpu_usage(self):
        """ Returns the cpu usage in the system """
        if self.get("cores") is None:
            self.call("cores")
        cores = self.get("cores")

        ps_out = run(["ps", "-e", "-o", "%cpu"]).strip().split("\n")[1:]
        cpu_usage = sum([float(i) for i in ps_out]) / cores
        return round(cpu_usage, self.options.cpu_usage_round)


    @abstractmethod
    def get_fan(self):
        """
        Abstract fan method to be implemented
        Returns the fan speed as an int
        """


    @abstractmethod
    def get_temp(self):
        """
        Abstract temp method to be implemented
        Returns the cpu temperature as a float
        """


    @abstractmethod
    def _get_uptime_sec(self):
        """
        Abstract uptime method to be implemented
        Returns the system uptime in seconds
        """


    def get_uptime(self):
        """ Formats system uptime """
        return unix_epoch_to_str(self._get_uptime_sec())


class AbstractMemory(AbstractGetter):
    """ Abstract memory class """

    @abstractmethod
    def get_used(self):
        """
        Abstract memory used method to be implemented
        Returns system used memory as a Storage class
        """


    @abstractmethod
    def get_total(self):
        """
        Abstract memory total method to be implemented
        Returns system total memory as a Storage class
        """


    def get_percent(self):
        """ Calculate the percentage of memory used """
        for i in ["used", "total"]:
            if self.get(i) is None:
                self.call(i)

        perc = percent(self.get("used"), self.get("total"))
        return round(perc, self.options.mem_percent_round)


class AbstractSwap(AbstractGetter):
    """ Abstract swap class """

    @abstractmethod
    def get_used(self):
        """
        Abstract swap used method to be implemented
        Returns system used swap as a Storage class
        """


    @abstractmethod
    def get_total(self):
        """
        Abstract swap total method to be implemented
        Returns system total swap as a Storage class
        """


    def get_percent(self):
        """ Calculate the percentage of swap used """
        for i in ["used", "total"]:
            if self.get(i) is None:
                self.call(i)

        perc = percent(self.get("used"), self.get("total"))
        return round(perc, self.options.swap_percent_round)


class AbstractDisk(AbstractGetter):
    """ Abstract disk class """

    def __init__(self, options):
        super().__init__(options)
        self.df_out = None


    def get_dev(self):
        """ Returns the device name of the disk """
        dev = None

        if self.options.disk is not None:
            reg = r"^({})".format(self.options.disk)
        else:
            self.df_flags.append(self.options.mount)
            reg = r"({})$".format(self.options.mount)
            reg = r"^([^\s]+)(\s+\d+%?){4}\s+" + reg

        self.df_out = run(self.df_flags).strip().split("\n")[1:]
        match = ([re.match(reg, line), line] for line in self.df_out)

        entry = next((i for i in match if i[0]), None)
        if entry is not None:
            dev = entry[0].group(1)
            self.df_out = entry[1].split()
            if self.options.disk_short_dev:
                dev = dev.split("/")[-1]

        return dev


    @abstractmethod
    def get_name(self):
        """
        Abstract disk name method to be implemented
        Returns the name of the disk as a string
        """


    @abstractmethod
    def get_mount(self):
        """
        Abstract disk mount method to be implemented
        Returns the mount location of the disk as a string
        """


    @abstractmethod
    def get_partition(self):
        """
        Abstract disk partition method to be implemented
        Returns the partition type of the disk as a string
        """


    def get_used(self):
        """
        Abstract disk used method to be implemented
        Returns system used disk as a Storage class
        """
        if self.df_out is None:
            self.get_dev()

        used = Storage(value=int(self.df_out[2]), prefix="KiB",
                       rounding=self.options.disk_used_round)
        used.set_prefix(self.options.disk_used_prefix)
        return used


    def get_total(self):
        """
        Abstract disk total method to be implemented
        Returns system total disk as a Storage class
        """
        if self.df_out is None:
            self.get_dev()

        total = Storage(value=int(self.df_out[1]), prefix="KiB",
                        rounding=self.options.disk_total_round)
        total.set_prefix(self.options.disk_total_prefix)
        return total


    def get_percent(self):
        """ Calculate the percentage of swap used """
        for i in ["used", "total"]:
            if self.get(i) is None:
                self.call(i)

        perc = percent(self.get("used"), self.get("total"))
        return round(perc, self.options.disk_percent_round)


class AbstractBattery(AbstractGetter):
    """ Abstract battery class """

    @abstractmethod
    def get_is_present(self):
        """
        Abstract method to determine if the system has a battery installed
        Returns a bool
        """


    @abstractmethod
    def get_is_charging(self):
        """
        Abstract method to determine if the battery is charging
        Returns a bool
        """


    @abstractmethod
    def get_is_full(self):
        """
        Abstract method to determine if the battery is full
        Returns a bool
        """


    @abstractmethod
    def get_percent(self):
        """
        Abstract method to calculate the battery percentage
        Returns a float
        """


    @abstractmethod
    def _get_time(self):
        """
        Abstract method to calculate battery time remaining
        Returns an int
        """


    def get_time(self):
        """ Formats battery time remaining """
        secs = self._get_time()
        secs = unix_epoch_to_str(secs) if secs != 0 else None
        return secs


    @abstractmethod
    def get_power(self):
        """
        Abstract method to calculate system power usage
        Returns a float, unit is watts
        """


class AbstractNetwork(AbstractGetter):
    """ Abstract network class """

    @abstractmethod
    def get_dev(self):
        """
        Abstract network device method to be implemented
        Returns a string
        """


    @abstractmethod
    def _get_ssid(self):
        """
        Abstract network ssid method to be implemented
        Returns a string
        """


    def get_ssid(self):
        """ Returns the network ssid as a string """
        ssid = None
        cmd, reg = self._get_ssid()
        if not (cmd is None or reg is None):
            ssid = (reg.match(i.strip()) for i in run(cmd).split("\n"))
            ssid = next((i.group(1) for i in ssid if i), None)

        return ssid


    def get_local_ip(self):
        """ Returns the network local ip as a string """
        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
        ip_out = run(self.local_ip_cmd + [dev]).strip().split("\n")
        ip_out = (reg.match(line.strip()) for line in ip_out)
        return next((i.group(1) for i in ip_out if i), None)


    @abstractmethod
    def _get_bytes_delta(self, dev, mode):
        """
        Abstract method to fetch change in bytes
        dev determines the device to check
        mode determines which delta bytes to find
        Returns an int
        """


    def __calc_bytes_delta_rate(self, mode):
        """
        Private method to calculate the rate of change in bytes
        Returns a float
        """
        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")
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


    def get_download(self):
        """
        Method to calculate network download speed
        Returns a Storage class
        """

        download = Storage(self.__calc_bytes_delta_rate("down"))
        download.set_prefix(self.options.net_download_prefix)
        return download


    def get_upload(self):
        """
        Method to calculate network upload speed
        Returns a Storage class
        """
        upload = Storage(self.__calc_bytes_delta_rate("up"))
        upload.set_prefix(self.options.net_upload_prefix)
        return upload


class Date(AbstractGetter):
    """ Date class to fetch date and time """

    def __init__(self, options):
        super().__init__(options)
        self.now = datetime.now()


    def get_date(self):
        """ Returns the date as a string from a specified format """
        fmt = "{{:{}}}".format(self.options.date_format)
        return fmt.format(self.now)


    def get_time(self):
        """ Returns the time as a string from a specified format """
        fmt = "{{:{}}}".format(self.options.time_format)
        return fmt.format(self.now)


class AbstractMisc(AbstractGetter):
    """ Misc class for fetching miscellaneous information """

    @abstractmethod
    def get_vol(self):
        """
        Abstract volume method to be implemented
        Returns a float
        """


    @abstractmethod
    def get_scr(self):
        """
        Abstract screen brightness method to be implemented
        Returns a float
        """
