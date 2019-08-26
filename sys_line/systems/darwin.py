#!/usr/bin/env python3
# pylint: disable=abstract-method
# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=no-self-use

""" Darwin specific module """

import re
import shutil
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
from ..tools.utils import percent, run, _round


class Darwin(System):
    """ A Darwin implementation of the abstract System class """

    def __init__(self, options: Namespace) -> None:
        super(Darwin, self).__init__(options,
                                     aux=SimpleNamespace(sysctl=Sysctl()),
                                     cpu=Cpu,
                                     mem=Memory,
                                     swap=Swap,
                                     disk=Disk,
                                     bat=Battery,
                                     net=Network,
                                     misc=Misc)


class Cpu(AbstractCpu):
    """ Darwin implementation of AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def cores(self) -> int:
        return int(self.aux.sysctl.query("hw.logicalcpu_max"))


    def _AbstractCpu__cpu_speed(self) -> (str, [float, int]):
        return self.aux.sysctl.query("machdep.cpu.brand_string"), None


    @property
    def load_avg(self) -> str:
        load = self.aux.sysctl.query("vm.loadavg").split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    @property
    def fan(self) -> int:
        fan = None
        if shutil.which("osx-cpu-temp"):
            regex = r"(\d+) RPM"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            fan = int(match.group(1)) if match else None

        return fan


    @property
    def temp(self) -> [float, int]:
        temp = None
        if shutil.which("osx-cpu-temp"):
            regex = r"CPU: ((\d+\.)?\d+)"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            temp = float(match.group(1)) if match else 0.0
            temp = _round(temp, self.options.cpu_temp_round)

        return temp


    def _AbstractCpu__uptime(self) -> int:
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(self.aux.sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ Darwin implementation of AbstractMemory class """

    @property
    def used(self) -> Storage:
        words = ["active", "wired down", "occupied by compressor"]
        vm_stat = run(["vm_stat"]).strip().split("\n")[1:]
        vm_stat = (re.sub(r"Pages |\.", r"", i) for i in vm_stat)
        vm_stat = dict(i.split(":", 1) for i in vm_stat)
        used = Storage(value=sum([int(vm_stat[i]) for i in words]) * 4096,
                       rounding=self.options.mem_used_round)
        used.prefix = self.options.mem_used_prefix

        return used


    @property
    def total(self) -> Storage:
        total = Storage(value=int(self.aux.sysctl.query("hw.memsize")),
                        rounding=self.options.mem_total_round)
        total.prefix = self.options.mem_total_prefix

        return total


class Swap(AbstractSwap):
    """ Darwin implementation of AbstractSwap class """

    @property
    @lru_cache(maxsize=1)
    def swapusage(self) -> str:
        """ Returns swapusage from sysctl """
        return self.aux.sysctl.query("vm.swapusage").strip()


    def __lookup_swap(self, search: str) -> int:
        value = 0

        regex = r"{} = (\d+\.\d+)M".format(search)
        match = re.search(regex, self.swapusage)

        if match:
            value = int(float(match.group(1)) * pow(1024, 2))

        return value


    @property
    def used(self) -> Storage:
        used = Storage(value=self.__lookup_swap("used"),
                       rounding=self.options.swap_used_round)
        used.prefix = self.options.swap_used_prefix

        return used


    @property
    def total(self) -> Storage:
        total = Storage(value=self.__lookup_swap("total"),
                        rounding=self.options.swap_total_round)
        total.prefix = self.options.swap_total_prefix

        return total


class Disk(AbstractDisk):
    """ Darwin implementation of AbstractDisk class """

    DF_FLAGS = ["df", "-P", "-k"]

    @property
    @lru_cache(maxsize=1)
    def diskutil(self) -> Dict[str, str]:
        """ Returns diskutil program output as a dict """
        dev = self.dev
        _diskutil = None
        if dev is not None:
            _diskutil = run(["diskutil", "info", self.dev]).split("\n")
            _diskutil = (re.sub(r"\s+", " ", i).strip() for i in _diskutil)
            _diskutil = dict(i.split(": ", 1) for i in _diskutil if i)

        return _diskutil


    def __lookup_diskutil(self, key: str) -> str:
        try:
            return self.diskutil[key]
        except KeyError:
            return None


    @property
    def name(self) -> str:
        return self.__lookup_diskutil("Volume Name")


    @property
    def partition(self) -> str:
        return self.__lookup_diskutil("File System Personality")


class Battery(AbstractBattery):
    """ Darwin implementation of AbstractBattery class """

    @property
    @lru_cache(maxsize=1)
    def bat(self) -> Dict[str, str]:
        """ Returns battery info from ioreg as a dict """
        _bat = run(["ioreg", "-rc", "AppleSmartBattery"]).split("\n")[1:]
        _bat = (re.sub("[\"{}]", "", i.strip()) for i in _bat)
        return dict(i.split(" = ", 1) for i in _bat if i.strip())


    @property
    @lru_cache(maxsize=1)
    def __current(self) -> int:
        current = 0
        if self.is_present:
            current = int(self.bat["InstantAmperage"])
            current -= pow(2, 64) if len(str(current)) >= 20 else 0
            current = abs(current)

        return current


    @property
    @lru_cache(maxsize=1)
    def __current_capacity(self) -> int:
        return int(self.bat["CurrentCapacity"]) if self.is_present else None


    @property
    @lru_cache(maxsize=1)
    def is_present(self) -> bool:
        return self.bat["BatteryInstalled"] == "Yes"


    @property
    def is_charging(self) -> bool:
        return self.bat["IsCharging"] == "Yes" if self.is_present else None


    @property
    def is_full(self) -> bool:
        return self.bat["FullyCharged"] == "Yes" if self.is_present else None


    @property
    def percent(self) -> [float, int]:
        perc = None

        if self.is_present:
            perc = percent(self.__current_capacity, int(self.bat["MaxCapacity"]))
            perc = _round(perc, self.options.bat_percent_round)

        return perc


    @property
    def _AbstractBattery__time(self) -> int:
        charge = None

        if self.is_present and self.current is not None:
            charge = self.current_capacity
            if self.is_charging:
                charge = int(self.bat["MaxCapacity"]) - charge
            charge = int((charge / self.current) * 3600)

        return charge


    @property
    def power(self) -> [float, int]:
        power = None

        if self.is_present:
            voltage = int(self.bat["Voltage"])
            power = (self.__current * voltage) / 1e6
            power = _round(power, self.options.bat_power_round)

        return power


class Network(AbstractNetwork):
    """ Darwin implementation of AbstractNetwork class """

    LOCAL_IP_CMD = ["ifconfig"]

    @property
    def dev(self) -> str:
        active = re.compile(r"status: active")
        dev_reg = re.compile(r"Device: (.*)$")
        check = lambda i: active.search(run(["ifconfig", i]))

        dev_list = run(["networksetup", "-listallhardwareports"])
        dev_list = dev_list.strip().split("\n")
        dev_list = (dev_reg.search(i) for i in dev_list)
        dev_list = (i.group(1) for i in dev_list if i)

        return next((i for i in dev_list if check(i)), None)


    @property
    def _AbstractNetwork__ssid(self) -> (List[str], RE_COMPILE):
        ssid_exe_path = ["System", "Library", "PrivateFrameworks",
                         "Apple80211.framework", "Versions", "Current",
                         "Resources", "airport"]
        ssid_exe = ["/{}".format("/".join(ssid_exe_path)), "--getinfo"]
        ssid_reg = re.compile("^SSID: (.*)$")

        return ssid_exe, ssid_reg


    def _AbstractNetwork__bytes_delta(self, dev: str, mode: str) -> int:
        cmd = ["netstat", "-nbiI", dev]
        reg = r"^({})(\s+[^\s]+){{{}}}\s+(\d+)"
        reg = reg.format(dev, 8 if mode == "up" else 5)
        reg = re.compile(reg)
        match = (reg.match(line) for line in run(cmd).split("\n"))

        return int(next((i.group(3) for i in match if i), 0))


class Misc(AbstractMisc):
    """ Darwin implementation of AbstractMisc class """

    @property
    def vol(self) -> [float, int]:
        cmd = ["vol"]
        osa = ["osascript", "-e", "output volume of (get volume settings)"]
        vol = float(run(cmd if shutil.which("vol") else osa))
        return _round(vol, self.options.misc_volume_round)


    @property
    def scr(self) -> [float, int]:
        scr = run(["ioreg", "-rc", "AppleBacklightDisplay"]).split("\n")
        scr = next((i for i in scr if "IODisplayParameters" in i), None)
        if scr is not None:
            scr = re.search(r"\"brightness\"=[^\=]+=(\d+),[^,]+,[^\=]+=(\d+)", scr)
            scr = percent(int(scr.group(2)), int(scr.group(1)))
            scr = _round(scr, self.options.misc_screen_round)

        return scr
