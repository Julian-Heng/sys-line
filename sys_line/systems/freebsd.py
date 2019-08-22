#!/usr/bin/env python3

""" FreeBSD specific module """

import re
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
from ..tools.utils import run, _round


class FreeBSD(System):
    """
    A FreeBSD implementation of the abstract
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
        super(FreeBSD, self).__init__(domains, os_name, options, aux)


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    def get_cores(self) -> int:
        return int(self.aux.sysctl.query("hw.ncpu"))


    def _get_cpu_speed(self) -> (str, [float, int]):
        cpu = self.aux.sysctl.query("hw.model")
        speed = self.aux.sysctl.query("hw.cpuspeed")
        if speed is None:
            speed = self.aux.sysctl.query("hw.clockrate")
        return cpu, _round(int(speed) / 1000, 2)


    def get_load_avg(self) -> str:
        load = self.aux.sysctl.query("vm.loadavg").split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    def get_fan(self) -> int:
        """ Stub """
        raise NotImplementedError


    def get_temp(self) -> float:
        temp = self.aux.sysctl.query("dev.cpu.0.temperature")
        temp = float(re.search(r"\d+\.?\d+", temp).group(0))
        return temp


    def _get_uptime_sec(self) -> int:
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(self.aux.sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    def get_used(self) -> Storage:
        total = int(self.aux.sysctl.query("hw.realmem"))
        pagesize = int(self.aux.sysctl.query("hw.pagesize"))

        keys = [int(self.aux.sysctl.query("vm.stats.vm.v_{}_count".format(i)))
                for i in ["inactive", "free", "cache"]]

        used = total - sum([i * pagesize for i in keys])
        used = Storage(value=used, prefix="B",
                       rounding=self.options.mem_used_round)
        used.set_prefix(self.options.mem_used_prefix)
        return used


    def get_total(self) -> Storage:
        total = int(self.aux.sysctl.query("hw.realmem"))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.mem_total_round)
        total.set_prefix(self.options.mem_total_prefix)
        return total


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    def get_used(self) -> Storage:
        extract = lambda i: int(i.split()[2])
        pstat = run(["pstat", "-s"]).strip().split("\n")[1:]
        pstat = sum([extract(i) for i in pstat])
        used = Storage(value=pstat, prefix="KiB",
                       rounding=self.options.swap_used_round)
        used.set_prefix(self.options.swap_used_prefix)
        return used


    def get_total(self) -> Storage:
        total = int(self.aux.sysctl.query("vm.swap_total"))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.swap_total_round)
        total.set_prefix(self.options.mem_total_prefix)
        return total


class Disk(AbstractDisk):
    """ FreeBSD implementation of AbstractDisk class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Disk, self).__init__(options, aux)
        self.df_flags = ["df", "-P", "-k"]


    def get_name(self) -> str:
        raise NotImplementedError


    def get_partition(self) -> str:
        partition = None

        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        dev = re.search(r"^(.*)p(\d+)$", dev)
        if dev is not None:
            gpart = run(["gpart", "show", dev.group(1)]).strip().split("\n")
            partition = gpart[int(dev.group(2))].split()[3]

        return partition


class Battery(AbstractBattery):
    """ FreeBSD implementation of AbstractBattery class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Battery, self).__init__(options, aux)

        bat = run(["acpiconf", "-i", "0"]).strip().split("\n")
        bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in bat]
        self.bat = dict(i.split(":", 1) for i in bat) if len(bat) > 1 else None


    def get_is_present(self) -> bool:
        return self.bat["State"] != "not present"


    def get_is_charging(self) -> bool:
        ret = None
        if self.call_get("is_present"):
            ret = self.bat["State"] == "charging"
        return ret


    def get_is_full(self) -> bool:
        ret = None
        if self.call_get("is_present"):
            ret = self.bat["State"] == "high"
        return ret


    def get_percent(self) -> int:
        ret = None
        if self.call_get("is_present"):
            ret = int(self.bat["Remaining capacity"][:-1])
        return ret


    def _get_time(self) -> int:
        secs = None
        if self.call_get("is_present"):
            acpi_time = self.bat["Remaining time"]
            if acpi_time != "unknown":
                acpi_time = [int(i) for i in acpi_time.split(":", maxsplit=3)]
                secs = acpi_time[0] * 3600 + acpi_time[1] * 60
            else:
                secs = 0

        return secs


    def get_power(self) -> float:
        ret = None
        if self.call_get("is_present"):
            ret = int(self.bat["Present rate"][:-3]) / 1000
        return ret


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    def __init__(self,
                 options: Namespace,
                 aux: SimpleNamespace = None) -> None:
        super(Network, self).__init__(options, aux)
        self.local_ip_cmd = ["ifconfig"]


    def get_dev(self) -> str:
        active = re.compile(r"^\s+status: associated$", re.M)
        dev_list = run(["ifconfig", "-l"]).split()
        check = lambda i, r=active: r.search(run(["ifconfig", i]))
        return next((i for i in dev_list if check(i)), None)


    def _get_ssid(self) -> (List[str], RE_COMPILE):
        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        ssid_reg = re.compile(r"ssid (.*) channel")
        ssid_exe = ["ifconfig", dev]

        return ssid_exe, ssid_reg


    def _get_bytes_delta(self, dev: str, mode: str) -> int:
        cmd = ["netstat", "-nbiI", dev]
        index = 10 if mode == "up" else 7
        return int(run(cmd).strip().split("\n")[1].split()[index])


class Misc(AbstractMisc):
    """ FreeBSD implementation of AbstractMisc class """

    def get_vol(self) -> [float, int]:
        raise NotImplementedError


    def get_scr(self) -> [float, int]:
        raise NotImplementedError
