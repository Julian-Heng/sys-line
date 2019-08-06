#!/usr/bin/env python3


""" FreeBSD specific module """

import re
import time

from .abstract import (System,
                       AbstractCpu,
                       AbstractMemory,
                       AbstractSwap,
                       AbstractDisk,
                       AbstractBattery,
                       AbstractNetwork,
                       AbstractMisc)

from ..tools.storage import Storage
from ..tools.utils import run


class FreeBSD(System):
    """
    A FreeBSD implementation of the abstract
    System class in abstract.py
    """

    def __init__(self, os_name, options):
        domains = {
            "cpu": Cpu,
            "mem": Memory,
            "swap": Swap,
            "disk": Disk,
            "bat": Battery,
            "net": Network,
            "misc": Misc
        }

        super(FreeBSD, self).__init__(domains, os_name, options)


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    def get_cores(self):
        return int(run(["sysctl", "-n", "hw.ncpu"]))


    def _get_cpu_speed(self):
        cpu, speed = run(["sysctl", "-n", "hw.model",
                          "hw.cpuspeed", "hw.clockrate"]).strip().split("\n")
        return cpu, int(speed) / 1000


    def get_load_avg(self):
        load = run(["sysctl", "-n", "vm.loadavg"]).split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    def get_fan(self):
        """ Stub """
        raise NotImplementedError


    def get_temp(self):
        return float(run(["sysctl", "-n", "dev.cpu.0.temperature"])[:-2])


    def _get_uptime_sec(self):
        cmd = ["sysctl", "-n", "kern.boottime"]
        regex = r"sec = (\d+),"
        return int(time.time()) - int(re.search(regex, run(cmd)).group(1))


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    def get_used(self):
        total = int(run(["sysctl", "-n", "hw.realmem"]))
        pagesize = int(run(["sysctl", "-n", "hw.pagesize"]))

        keys = [["sysctl", "-n", "vm.stats.vm.v_{}_count".format(i)]
                for i in ["inactive", "free", "cache"]]

        used = total - sum([int(run(i)) * pagesize for i in keys])
        used = Storage(value=used, prefix="B",
                       rounding=self.options.mem_used_round)
        used.set_prefix(self.options.mem_used_prefix)
        return used


    def get_total(self):
        total = int(run(["sysctl", "-n", "hw.realmem"]))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.mem_total_round)
        total.set_prefix(self.options.mem_total_prefix)
        return total


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    def get_used(self):
        extract = lambda i: int(i.split()[2])
        pstat = run(["pstat", "-s"]).strip().split("\n")[1:]
        pstat = sum([extract(i) for i in pstat])
        used = Storage(value=pstat, prefix="KiB",
                       rounding=self.options.swap_used_round)
        used.set_prefix(self.options.swap_used_prefix)
        return used


    def get_total(self):
        total = int(run(["sysctl", "-n", "vm.swap_total"]))
        total = Storage(value=total, prefix="B",
                        rounding=self.options.swap_total_round)
        total.set_prefix(self.options.mem_total_prefix)
        return total


class Disk(AbstractDisk):
    """ FreeBSD implementation of AbstractDisk class """

    def __init__(self, options):
        super(Disk, self).__init__(options)
        self.df_flags = ["df", "-P", "-k"]


    def get_name(self):
        raise NotImplementedError


    def get_partition(self):
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

    def __init__(self, options):
        super(Battery, self).__init__(options)

        bat = run(["acpiconf", "-i", "0"]).strip().split("\n")
        bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in bat]
        self.bat = dict(i.split(":", 1) for i in bat) if len(bat) > 1 else None


    def get_is_present(self):
        return self.bat is not None


    def get_is_charging(self):
        return self.bat["State"] == "charging"


    def get_is_full(self):
        return self.bat["State"] == "high"


    def get_percent(self):
        return int(self.bat["Remaining capacity"][:-1])


    def _get_time(self):
        secs = None
        acpi_time = self.bat["Remaining secs"]
        if acpi_time != "unknown":
            acpi_time = [int(i) for i in acpi_time.split(":", maxsplit=3)]
            secs = acpi_time[0] * 3600 + acpi_time[1] * 60
        else:
            secs = 0

        return secs


    def get_power(self):
        return int(self.bat["Present rate"][:-3]) / 1000


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    def get_dev(self):
        active = re.compile(r"^\s+status: associated$", re.M)
        dev_list = run(["ifconfig", "-l"]).split()
        check = lambda i, r=active: r.search(run(["ifconfig", i]))
        return next((i for i in dev_list if check(i)), None)


    def _get_ssid(self):
        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        ssid_reg = re.compile(r"ssid (.*) channel")
        ssid_exe = ["ifconfig", dev]

        return ssid_exe, ssid_reg


    def _get_bytes_delta(self, dev, mode):
        cmd = ["netstat", "-nbiI", dev]
        index = 10 if mode == "up" else 7
        return int(run(cmd).strip().split("\n")[1].split()[index])


class Misc(AbstractMisc):
    """ FreeBSD implementation of AbstractMisc class """

    def get_vol(self):
        raise NotImplementedError


    def get_scr(self):
        raise NotImplementedError
