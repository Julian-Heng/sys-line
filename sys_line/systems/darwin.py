#!/usr/bin/env python3

""" Darwin specific module """

import re
import shutil
import time

from argparse import Namespace
from types import SimpleNamespace
from typing import List

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
    """
    A Darwin implementation of the abstract
    System class in abstract.py
    """

    def __init__(self, os_name: str, options: Namespace) -> None:
        domains = {
            "cpu": Cpu,
            "mem": Memory,
            "swap": Swap,
            "disk": Disk,
            "bat": Battery,
            "net": Network,
            "misc": Misc
        }

        aux = SimpleNamespace(sysctl=Sysctl())
        super(Darwin, self).__init__(domains, os_name, options, aux)


class Cpu(AbstractCpu):
    """ Darwin implementation of AbstractCpu class """

    def get_cores(self) -> int:
        return int(self.aux.sysctl.query("hw.logicalcpu_max"))


    def _get_cpu_speed(self) -> (str, float):
        return self.aux.sysctl.query("machdep.cpu.brand_string"), None


    def get_load_avg(self) -> str:
        load = self.aux.sysctl.query("vm.loadavg").split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    def get_fan(self) -> int:
        fan = None
        if shutil.which("osx-cpu-temp"):
            regex = r"(\d+) RPM"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            fan = int(match.group(1)) if match else None

        return fan


    def get_temp(self) -> [float, int]:
        temp = None
        if shutil.which("osx-cpu-temp"):
            regex = r"CPU: ((\d+\.)?\d+)"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            temp = float(match.group(1)) if match else 0.0
            temp = _round(temp, self.options.cpu_temp_round)

        return temp


    def _get_uptime_sec(self) -> int:
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(self.aux.sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ Darwin implementation of AbstractMemory class """

    def get_used(self) -> Storage:
        words = ["active", "wired down", "occupied by compressor"]
        vm_stat = run(["vm_stat"]).strip().split("\n")[1:]
        vm_stat = (re.sub(r"Pages |\.", r"", i) for i in vm_stat)
        vm_stat = dict(i.split(":", 1) for i in vm_stat)
        used = Storage(value=sum([int(vm_stat[i]) for i in words]) * 4096,
                       rounding=self.options.mem_used_round)
        used.prefix = self.options.mem_used_prefix

        return used


    def get_total(self) -> Storage:
        total = Storage(value=int(self.aux.sysctl.query("hw.memsize")),
                        rounding=self.options.mem_total_round)
        total.prefix = self.options.mem_total_prefix

        return total


class Swap(AbstractSwap):
    """ Darwin implementation of AbstractSwap class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Swap, self).__init__(options, aux)
        self.swapusage = None


    def __lookup_swap(self, search: str) -> int:
        value = 0

        if self.swapusage is None:
            self.swapusage = self.aux.sysctl.query("vm.swapusage").strip()

        regex = r"{} = (\d+\.\d+)M".format(search)
        match = re.search(regex, self.swapusage)

        if match:
            value = int(float(match.group(1)) * pow(1024, 2))

        return value


    def get_used(self) -> Storage:
        used = Storage(value=self.__lookup_swap("used"),
                       rounding=self.options.swap_used_round)
        used.prefix = self.options.swap_used_prefix

        return used


    def get_total(self) -> Storage:
        total = Storage(value=self.__lookup_swap("total"),
                        rounding=self.options.swap_total_round)
        total.prefix = self.options.swap_total_prefix

        return total


class Disk(AbstractDisk):
    """ Darwin implementation of AbstractDisk class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Disk, self).__init__(options, aux)
        self.df_flags = ["df", "-P", "-k"]
        self.diskutil = None


    def __set_diskutil(self) -> None:
        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        diskutil = run(["diskutil", "info", self.get("dev")]).split("\n")
        diskutil = (re.sub(r"\s+", " ", i).strip() for i in diskutil)
        self.diskutil = dict(i.split(": ", 1) for i in diskutil if i)


    def __lookup_diskutil(self, key: str) -> str:
        if not self.diskutil:
            self.__set_diskutil()

        return self.diskutil[key]


    def get_name(self) -> str:
        return self.__lookup_diskutil("Volume Name")


    def get_partition(self) -> str:
        return self.__lookup_diskutil("File System Personality")


class Battery(AbstractBattery):
    """ Darwin implementation of AbstractBattery class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Battery, self).__init__(options, aux)

        bat = run(["ioreg", "-rc", "AppleSmartBattery"]).split("\n")[1:]
        bat = (re.sub("[\"{}]", "", i.strip()) for i in bat)
        self.bat = dict(i.split(" = ", 1) for i in bat if i.strip())

        self.current = None
        self.current_capacity = None


    def get_is_present(self) -> bool:
        return self.bat["BatteryInstalled"] == "Yes"


    def get_is_charging(self) -> bool:
        ret = None
        if self.call_get("is_present"):
            ret = self.bat["IsCharging"] == "Yes"
        return ret


    def get_is_full(self) -> bool:
        ret = None
        if self.call_get("is_present"):
            ret = self.bat["FullyCharged"] == "Yes"
        return ret


    def get_percent(self) -> [float, int]:
        perc = None
        if self.call_get("is_present"):
            if self.current_capacity is None:
                self.__get_current_capacity()

            perc = percent(self.current_capacity, int(self.bat["MaxCapacity"]))
            perc = _round(perc, self.options.bat_percent_round)

        return perc


    def _get_time(self) -> int:
        charge = None

        if self.call_get("is_present"):
            if self.current_capacity is None:
                self.__get_current_capacity()
            if self.current is None:
                self.__get_amperage()
            if self.current == 0:
                return 0

            charge = self.current_capacity
            if self.get_is_charging():
                charge = int(self.bat["MaxCapacity"]) - charge
            charge = int((charge / self.current) * 3600)

        return charge


    def get_power(self) -> [float, int]:
        power = None

        if self.call_get("is_present"):
            if self.current is None:
                self.__get_amperage()

            voltage = int(self.bat["Voltage"])
            power = (self.current * voltage) / 1e6
            power = _round(power, self.options.bat_power_round)

        return power


    def __get_current_capacity(self) -> None:
        if self.call_get("is_present"):
            self.current_capacity = int(self.bat["CurrentCapacity"])


    def __get_amperage(self) -> None:
        if self.call_get("is_present"):
            current = int(self.bat["InstantAmperage"])
            current -= pow(2, 64) if len(str(current)) >= 20 else 0
            self.current = abs(current)


class Network(AbstractNetwork):
    """ Darwin implementation of AbstractNetwork class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Network, self).__init__(options, aux)
        self.local_ip_cmd = ["ifconfig"]


    def get_dev(self) -> str:
        active = re.compile(r"status: active")
        dev_reg = re.compile(r"Device: (.*)$")
        check = lambda i, r=active: r.search(run(["ifconfig", i]))

        dev_list = run(["networksetup", "-listallhardwareports"])
        dev_list = dev_list.strip().split("\n")
        dev_list = (dev_reg.search(i) for i in dev_list)
        dev_list = (i.group(1) for i in dev_list if i)

        return next((i for i in dev_list if check(i)), None)


    def _get_ssid(self) -> (List[str], RE_COMPILE):
        ssid_exe = "/System/Library/PrivateFrameworks/Apple80211.framework"
        ssid_exe = "{}/Versions/Current/Resources/airport".format(ssid_exe)
        ssid_exe = [ssid_exe, "--getinfo"]
        ssid_reg = re.compile("^SSID: (.*)$")

        return ssid_exe, ssid_reg


    def _get_bytes_delta(self, dev: str, mode: str) -> int:
        cmd = ["netstat", "-nbiI", dev]
        reg = r"^({})(\s+[^\s]+){{{}}}\s+(\d+)"
        reg = reg.format(dev, 8 if mode == "up" else 5)
        reg = re.compile(reg)
        match = (reg.match(line) for line in run(cmd).split("\n"))

        return int(next((i.group(3) for i in match if i), 0))


class Misc(AbstractMisc):
    """ Darwin implementation of AbstractMisc class """

    def get_vol(self) -> [float, int]:
        cmd = ["vol"]
        osa = ["osascript", "-e", "output volume of (get volume settings)"]
        vol = float(run(cmd if shutil.which("vol") else osa))
        return _round(vol, self.options.misc_volume_round)


    def get_scr(self) -> [float, int]:
        scr = run(["ioreg", "-rc", "AppleBacklightDisplay"]).split("\n")
        scr = next((i for i in scr if "IODisplayParameters" in i), None)
        if scr is not None:
            scr = re.search(r"\"brightness\"=[^\=]+=(\d+),[^,]+,[^\=]+=(\d+)", scr)
            scr = percent(int(scr.group(2)), int(scr.group(1)))
            scr = _round(scr, self.options.misc_screen_round)

        return scr
