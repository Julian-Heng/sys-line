#!/usr/bin/env python3
# pylint: disable=invalid-name

""" FreeBSD specific module """

import re
import time

from functools import lru_cache
from types import SimpleNamespace

from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from ..tools.sysctl import Sysctl
from ..tools.utils import run, _round


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def cores(self):
        return int(self.aux.sysctl.query("hw.ncpu"))

    def _cpu_speed(self):
        cpu = self.aux.sysctl.query("hw.model")
        speed = self.aux.sysctl.query("hw.cpuspeed")
        if speed is None:
            speed = self.aux.sysctl.query("hw.clockrate")
        return cpu, _round(int(speed) / 1000, 2)

    def _load_avg(self):
        return self.aux.sysctl.query("vm.loadavg").split()[1:4]

    @property
    def fan(self):
        """ Stub """
        return None

    @property
    def temp(self):
        temp = self.aux.sysctl.query("dev.cpu.0.temperature")
        return float(re.search(r"\d+\.?\d+", temp).group(0)) if temp else None

    def _uptime(self):
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(self.aux.sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    def _used(self):
        total = int(self.aux.sysctl.query("hw.realmem"))
        pagesize = int(self.aux.sysctl.query("hw.pagesize"))

        keys = [int(self.aux.sysctl.query("vm.stats.vm.v_{}_count".format(i)))
                for i in ["inactive", "free", "cache"]]

        used = total - sum([i * pagesize for i in keys])
        return used, "B"

    def _total(self):
        return int(self.aux.sysctl.query("hw.realmem")), "B"


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    def _used(self):
        extract = lambda i: int(i.split()[2])
        pstat = run(["pstat", "-s"]).strip().split("\n")[1:]
        pstat = sum([extract(i) for i in pstat])
        return pstat, "KiB"

    def _total(self):
        return int(self.aux.sysctl.query("vm.swap_total")), "B"


class Disk(AbstractDisk):
    """ FreeBSD implementation of AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P", "-k"]

    @property
    def name(self):
        """ Stub """
        return {i: None for i in self.original_dev.keys()}

    @property
    def partition(self):
        partition = None
        gpart_out = dict()
        reg = re.compile(r"^(.*)p(\d+)$")
        dev_reg = {i: reg.search(i) for i in self.original_dev.keys()}

        if dev_reg:
            partition = dict()
            for k, v in dev_reg.items():
                if v is not None:
                    if k not in gpart_out.keys():
                        gpart_cmd = ["gpart", "show", "-p", v.group(1)]
                        gpart_out[k] = run(gpart_cmd).strip().split("\n")

                    geom = v.group(0).split("/")[-1]
                    out = next((i for i in gpart_out[k] if geom in i), None)
                    partition[k] = None if out is None else out.split()[3]

        return partition


class Battery(AbstractBattery):
    """ FreeBSD implementation of AbstractBattery class """

    @property
    @lru_cache(maxsize=1)
    def bat(self):
        """ Returns battery info from acpiconf as dict """
        bat = run(["acpiconf", "-i", "0"]).strip().split("\n")
        bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in bat]
        return dict(i.split(":", 1) for i in bat) if len(bat) > 1 else None

    @property
    def is_present(self):
        return self.bat["State"] != "not present" if self.bat else False

    @property
    def is_charging(self):
        return self.bat["State"] == "charging" if self.is_present else None

    @property
    def is_full(self):
        return self.bat["State"] == "high" if self.is_present else None

    @property
    def percent(self):
        ret = None
        if self.is_present:
            ret = int(self.bat["Remaining capacity"][:-1])
        return ret

    @property
    def _time(self):
        secs = 0
        if self.is_present:
            acpi_time = self.bat["Remaining time"]
            if acpi_time != "unknown":
                acpi_time = [int(i) for i in acpi_time.split(":", maxsplit=3)]
                secs = acpi_time[0] * 3600 + acpi_time[1] * 60
            else:
                secs = 0

        return secs

    @property
    def power(self):
        ret = None
        if self.is_present:
            ret = int(self.bat["Present rate"][:-3]) / 1000
        return ret


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ifconfig"]

    @property
    def dev(self):
        active = re.compile(r"^\s+status: (associated|active)$", re.M)
        dev_list = run(self._LOCAL_IP_CMD + ["-l"]).split()
        check = lambda i: active.search(run(self._LOCAL_IP_CMD + [i]))
        return next((i for i in dev_list if check(i)), None)

    @property
    def _ssid(self):
        ssid_cmd = tuple(self._LOCAL_IP_CMD + [self.dev])
        ssid_reg = re.compile(r"ssid (.*) channel")
        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        cmd = ["netstat", "-nbiI", dev]
        index = 10 if mode == "up" else 7
        return int(run(cmd).strip().split("\n")[1].split()[index])


class Misc(AbstractMisc):
    """ FreeBSD implementation of AbstractMisc class """

    @property
    def vol(self):
        """ Stub """
        return None

    @property
    def scr(self):
        """ Stub """
        return None


class FreeBSD(System):
    """ A FreeBSD implementation of the abstract System class """

    def __init__(self, options):
        super(FreeBSD, self).__init__(options,
                                      aux=SimpleNamespace(sysctl=Sysctl()),
                                      cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                      bat=Battery, net=Network, misc=Misc)
