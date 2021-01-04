#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=invalid-name

""" FreeBSD specific module """

import re
import time

from functools import lru_cache

from . import wm
from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from ..tools.sysctl import Sysctl
from ..tools.utils import run, round_trim


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    def cores(self, options=None):
        return int(Sysctl.query("hw.ncpu"))

    def _cpu_string(self):
        return Sysctl.query("hw.model")

    def _cpu_speed(self):
        speed = Sysctl.query("hw.cpuspeed")
        if speed is None:
            speed = Sysctl.query("hw.clockrate")
        return round_trim(int(speed) / 1000, 2)

    def _load_avg(self):
        return Sysctl.query("vm.loadavg").split()[1:4]

    def fan(self, options=None):
        """ Stub """
        return None

    def _temp(self):
        temp = Sysctl.query("dev.cpu.0.temperature")
        return float(re.search(r"\d+\.?\d+", temp).group(0)) if temp else None

    def _uptime(self):
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(Sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    def _used(self):
        total = int(Sysctl.query("hw.realmem"))
        pagesize = int(Sysctl.query("hw.pagesize"))

        keys = [int(Sysctl.query(f"vm.stats.vm.v_{i}_count"))
                for i in ["inactive", "free", "cache"]]

        used = total - sum(i * pagesize for i in keys)
        return used, "B"

    def _total(self):
        return int(Sysctl.query("hw.realmem")), "B"


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    def _used(self):
        def extract(line):
            return int(line.split()[2])

        pstat = run(["pstat", "-s"]).strip().split("\n")[1:]
        pstat = sum(extract(i) for i in pstat)
        return pstat, "KiB"

    def _total(self):
        return int(Sysctl.query("vm.swap_total")), "B"


class Disk(AbstractDisk):
    """ FreeBSD implementation of AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P", "-k"]

    def name(self, options=None):
        """ Stub """
        return {i: None for i in self._original_dev(options).keys()}

    def partition(self, options=None):
        devs = self._original_dev(options)
        partition = None
        gpart_out = dict()
        reg = re.compile(r"^(.*)p(\d+)$")
        dev_reg = {i: reg.search(i) for i in devs.keys()}

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

    def is_present(self, options=None):
        acpiconf = Battery.acpiconf()
        return acpiconf["State"] != "not present" if acpiconf else False

    def is_charging(self, options=None):
        acpiconf = Battery.acpiconf()
        is_present = self.is_present(options)
        return acpiconf["State"] == "charging" if is_present else None

    def is_full(self, options=None):
        acpiconf = Battery.acpiconf()
        is_present = self.is_present(options)
        return acpiconf["State"] == "high" if is_present else None

    def percent(self, options=None):
        ret = None
        is_present = self.is_present(options)
        if is_present:
            acpiconf = Battery.acpiconf()
            ret = int(acpiconf["Remaining capacity"][:-1])
        return ret

    def _time(self):
        secs = 0
        is_present = self.is_present(None)
        if is_present:
            acpiconf = Battery.acpiconf()
            acpi_time = acpiconf["Remaining time"]
            if acpi_time != "unknown":
                acpi_time = [int(i) for i in acpi_time.split(":", maxsplit=3)]
                secs = acpi_time[0] * 3600 + acpi_time[1] * 60
            else:
                secs = 0

        return secs

    def power(self, options=None):
        ret = None
        is_present = self.is_present(options)
        if is_present:
            acpiconf = Battery.acpiconf()
            ret = int(acpiconf["Present rate"][:-3]) / 1000
        return ret

    @staticmethod
    @lru_cache(maxsize=1)
    def acpiconf():
        """ Returns battery info from acpiconf as dict """
        bat = run(["acpiconf", "-i", "0"]).strip().split("\n")
        bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in bat]
        return dict(i.split(":", 1) for i in bat) if len(bat) > 1 else None


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ifconfig"]

    def dev(self, options=None):
        def check(dev):
            return active.search(run(self._LOCAL_IP_CMD + [dev]))

        active = re.compile(r"^\s+status: (associated|active)$", re.M)
        dev_list = run(self._LOCAL_IP_CMD + ["-l"]).split()
        return next((i for i in dev_list if check(i)), None)

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

    def _vol(self):
        """ Stub """
        return None

    def _scr(self):
        """ Stub """
        return None


class FreeBSD(System):
    """ A FreeBSD implementation of the abstract System class """

    def __init__(self, default_options):
        super(FreeBSD, self).__init__(default_options,
                                      cpu=Cpu, mem=Memory, swap=Swap,
                                      disk=Disk, bat=Battery, net=Network,
                                      wm=self.detect_window_manager(),
                                      misc=Misc)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "Xorg": wm.Xorg,
        }
