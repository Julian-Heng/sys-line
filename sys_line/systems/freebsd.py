#!/usr/bin/env python3
# pylint: disable=abstract-method
# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=no-self-use

""" FreeBSD specific module """

import re
import time

from argparse import Namespace
from functools import lru_cache
from types import SimpleNamespace
from typing import Dict, List

from .abstract import (RE_COMPILE,
                       System,
                       AbstractCpu,
                       AbstractMemory,
                       AbstractSwap,
                       AbstractDisk,
                       AbstractBattery,
                       AbstractNetwork,
                       AbstractMisc)
from ..tools.storage import Storage
from ..tools.sysctl import Sysctl
from ..tools.utils import run, _round


class FreeBSD(System):
    """ A FreeBSD implementation of the abstract System class """

    def __init__(self, options: Namespace) -> None:
        super(FreeBSD, self).__init__(options,
                                      aux=SimpleNamespace(sysctl=Sysctl()),
                                      cpu=Cpu,
                                      mem=Memory,
                                      swap=Swap,
                                      disk=Disk,
                                      bat=Battery,
                                      net=Network,
                                      misc=Misc)


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def cores(self) -> int:
        return int(self.aux.sysctl.query("hw.ncpu"))


    def _AbstractCpu__cpu_speed(self) -> (str, [float, int]):
        cpu = self.aux.sysctl.query("hw.model")
        speed = self.aux.sysctl.query("hw.cpuspeed")
        if speed is None:
            speed = self.aux.sysctl.query("hw.clockrate")
        return cpu, _round(int(speed) / 1000, 2)


    @property
    def load_avg(self) -> str:
        load = self.aux.sysctl.query("vm.loadavg").split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    @property
    def fan(self) -> int:
        """ Stub """
        return None


    @property
    def temp(self) -> float:
        temp = self.aux.sysctl.query("dev.cpu.0.temperature")
        temp = float(re.search(r"\d+\.?\d+", temp).group(0))
        return temp


    def _AbstractCpu__uptime(self) -> int:
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(self.aux.sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    @property
    def used(self) -> Storage:
        total = int(self.aux.sysctl.query("hw.realmem"))
        pagesize = int(self.aux.sysctl.query("hw.pagesize"))

        keys = [int(self.aux.sysctl.query("vm.stats.vm.v_{}_count".format(i)))
                for i in ["inactive", "free", "cache"]]

        used = total - sum([i * pagesize for i in keys])
        used = Storage(value=used, prefix="B",
                       rounding=self.options.mem_used_round)
        used.prefix = self.options.mem_used_prefix
        return used


    @property
    def total(self) -> Storage:
        total = int(self.aux.sysctl.query("hw.realmem"))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.mem_total_round)
        total.prefix = self.options.mem_total_prefix
        return total


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    @property
    def used(self) -> Storage:
        extract = lambda i: int(i.split()[2])
        pstat = run(["pstat", "-s"]).strip().split("\n")[1:]
        pstat = sum([extract(i) for i in pstat])
        used = Storage(value=pstat, prefix="KiB",
                       rounding=self.options.swap_used_round)
        used.prefix = self.options.swap_used_prefix
        return used


    @property
    def total(self) -> Storage:
        total = int(self.aux.sysctl.query("vm.swap_total"))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.swap_total_round)
        total.prefix = self.options.swap_total_prefix
        return total


class Disk(AbstractDisk):
    """ FreeBSD implementation of AbstractDisk class """

    DF_FLAGS = ["df", "-P", "-k"]

    @property
    def name(self) -> str:
        """ Stub """
        return None


    @property
    def partition(self) -> str:
        partition = None
        dev = re.search(r"^(.*)p(\d+)$", self.dev)

        if dev is not None:
            gpart = run(["gpart", "show", dev.group(1)]).strip().split("\n")
            partition = gpart[int(dev.group(2))].split()[3]

        return partition


class Battery(AbstractBattery):
    """ FreeBSD implementation of AbstractBattery class """

    @property
    @lru_cache(maxsize=1)
    def bat(self) -> Dict[str, str]:
        """ Returns battery info from acpiconf as dict """
        _bat = run(["acpiconf", "-i", "0"]).strip().split("\n")
        _bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in _bat]
        return dict(i.split(":", 1) for i in _bat) if len(_bat) > 1 else None


    @property
    def is_present(self) -> bool:
        return self.bat["State"] != "not present"


    @property
    def is_charging(self) -> bool:
        return self.bat["State"] == "charging" if self.is_present else None


    @property
    def is_full(self) -> bool:
        return self.bat["State"] == "high" if self.is_present else None


    @property
    def percent(self) -> int:
        ret = None
        if self.is_present:
            ret = int(self.bat["Remaining capacity"][:-1])
        return ret


    def _AbstractBattery__time(self) -> int:
        secs = None
        if self.call_get("is_present"):
            acpi_time = self.bat["Remaining time"]
            if acpi_time != "unknown":
                acpi_time = [int(i) for i in acpi_time.split(":", maxsplit=3)]
                secs = acpi_time[0] * 3600 + acpi_time[1] * 60
            else:
                secs = 0

        return secs


    @property
    def power(self) -> float:
        ret = None
        if self.is_present:
            ret = int(self.bat["Present rate"][:-3]) / 1000
        return ret


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    LOCAL_IP_CMD = ["ifconfig"]

    @property
    def dev(self) -> str:
        active = re.compile(r"^\s+status: associated$", re.M)
        dev_list = run(["ifconfig", "-l"]).split()
        check = lambda i, r=active: r.search(run(["ifconfig", i]))
        return next((i for i in dev_list if check(i)), None)


    @property
    def _AbstractNetwork__ssid(self) -> (List[str], RE_COMPILE):
        ssid_reg = re.compile(r"ssid (.*) channel")
        ssid_exe = ["ifconfig", self.dev]
        return ssid_exe, ssid_reg


    def _AbstractNetwork__bytes_delta(self, dev: str, mode: str) -> int:
        cmd = ["netstat", "-nbiI", dev]
        index = 10 if mode == "up" else 7
        return int(run(cmd).strip().split("\n")[1].split()[index])


class Misc(AbstractMisc):
    """ FreeBSD implementation of AbstractMisc class """

    @property
    def vol(self) -> [float, int]:
        """ Stub """
        return None


    @property
    def scr(self) -> [float, int]:
        """ Stub """
        return None
