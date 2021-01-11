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
from logging import getLogger

from . import wm
from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from ..tools.sysctl import Sysctl
from ..tools.utils import run, round_trim


LOG = getLogger(__name__)


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    def cores(self, options=None):
        return int(Sysctl.query("hw.ncpu"))

    def _cpu_string(self):
        return Sysctl.query("hw.model")

    def _cpu_speed(self):
        speed = Sysctl.query("hw.cpuspeed")
        if speed is None:
            LOG.debug("trying 'hw.clockrate'")
            speed = Sysctl.query("hw.clockrate")
        return round_trim(int(speed) / 1000, 2)

    def _load_avg(self):
        query = Sysctl.query("vm.loadavg")
        if query is None:
            return None

        return query.split()[1:4]

    def fan(self, options=None):
        """ Stub """
        LOG.debug("freebsd fan is not implemented")

    def _temp(self):
        temp = Sysctl.query("dev.cpu.0.temperature")
        if temp is None:
            return None

        reg = re.compile(r"\d+\.?\d+")
        temp = reg.search(temp)
        if temp is None:
            LOG.debug("unable to match temp regex")
            return None

        return float(temp.group(0))

    def _uptime(self):
        reg = re.compile(r"sec = (\d+),")
        query = Sysctl.query("kern.boottime")
        if query is None:
            return 0

        sec = reg.search(query).group(1)
        sec = int(time.time()) - int(sec)
        return sec


class Memory(AbstractMemory):
    """ FreeBSD implementation of AbstractMemory class """

    def _used(self):
        total = int(Sysctl.query("hw.realmem", default=0))
        pagesize = int(Sysctl.query("hw.pagesize", default=0))

        keys = [int(Sysctl.query(f"vm.stats.vm.v_{i}_count", default=0))
                for i in ["inactive", "free", "cache"]]

        used = total
        used -= sum(i * pagesize for i in keys)
        return used, "B"

    def _total(self):
        total = int(Sysctl.query("hw.realmem", default=0))
        return total, "B"


class Swap(AbstractSwap):
    """ FreeBSD implementation of AbstractSwap class """

    def _used(self):
        def extract(line):
            return int(line.split()[2])

        pstat = run(["pstat", "-s"])
        if pstat is None:
            return 0, "B"

        pstat = pstat.strip().splitlines()[1:]
        pstat = sum(extract(i) for i in pstat)
        return pstat, "KiB"

    def _total(self):
        return int(Sysctl.query("vm.swap_total", default=0)), "B"


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
        if devs is None:
            LOG.debug("unable to get disk devices")
            return None

        reg = re.compile(r"^(.*)p(\d+)$")
        dev_reg = {i: reg.search(i) for i in devs.keys()}

        if not dev_reg:
            LOG.debug("unable to match disk regex")
            return None

        partition = {k: None for k in devs.keys()}
        gpart_out = dict()
        for k, v in dev_reg.items():
            if v is None:
                continue

            if k not in gpart_out.keys():
                LOG.debug("'%s' is not cached, caching...", k)
                gpart_cmd = ["gpart", "show", "-p", v.group(1)]
                out = run(gpart_cmd)
                if not out:
                    LOG.debug("unable to get output from gpart on '%s'", k)
                    continue

                gpart_out[k] = out.strip().splitlines()

            geom = v.group(0).split("/")[-1]
            out = next((i for i in gpart_out[k] if geom in i), None)
            if not out:
                LOG.debug("geom is not valid for '%s'", k)
            else:
                partition[k] = out.split()[3]

        return partition


class Battery(AbstractBattery):
    """ FreeBSD implementation of AbstractBattery class """

    def is_present(self, options=None):
        acpiconf = Battery.acpiconf()
        if acpiconf is None:
            LOG.debug("unable to get acpiconf output")
            return False

        return acpiconf.get("State", "") != "not present"

    def is_charging(self, options=None):
        acpiconf = Battery.acpiconf()
        is_present = self.is_present(options)

        if acpiconf is None:
            LOG.debug("unable to get acpiconf output")
            return None

        if not is_present:
            LOG.debug("battery is not present")
            return None

        return acpiconf.get("State", "") == "charging"

    def is_full(self, options=None):
        acpiconf = Battery.acpiconf()
        is_present = self.is_present(options)
        if acpiconf is None or not is_present:
            return None

        return acpiconf.get("State", "") == "high"

    def _percent(self):
        pass

    def percent(self, options=None):
        acpiconf = Battery.acpiconf()
        is_present = self.is_present(options)

        if acpiconf is None:
            LOG.debug("unable to get acpiconf output")
            return None

        if not is_present:
            LOG.debug("battery is not present")
            return None

        if "Remaining capacity" not in acpiconf:
            LOG.debug("acpiconf does not contain key 'Remaining capacity'")
            return None

        return int(acpiconf["Remaining capacity"][:-1])

    def _time(self):
        is_present = self.is_present(None)
        acpiconf = Battery.acpiconf()

        if acpiconf is None:
            LOG.debug("unable to get acpiconf output")
            return 0

        if not is_present:
            LOG.debug("battery is not present")
            return 0

        acpi_time = acpiconf.get("Remaining time", "")
        if acpi_time != "unknown":
            acpi_time = [int(i) for i in acpi_time.split(":", 3)]
            secs = (acpi_time[0] * 3600) + (acpi_time[1] * 60)
        else:
            secs = 0

        return secs

    def _power(self):
        pass

    def power(self, options=None):
        is_present = self.is_present(options)
        acpiconf = Battery.acpiconf()

        if acpiconf is None:
            LOG.debug("unable to get acpiconf output")
            return None

        if not is_present:
            LOG.debug("battery is not present")
            return None

        if "Present rate" not in acpiconf:
            LOG.debug("acpiconf does not contain key 'Present rate'")
            return None

        power = int(acpiconf["Present rate"][:-3]) / 1000
        return power

    @staticmethod
    @lru_cache(maxsize=1)
    def acpiconf():
        """ Returns battery info from acpiconf as dict """
        bat = run(["acpiconf", "-i", "0"])
        if bat is None:
            return None

        bat = bat.strip().splitlines()
        bat = [re.sub(r"(:)\s+", r"\g<1>", i) for i in bat]
        if len(bat) == 0:
            return None

        return dict(i.split(":", 1) for i in bat)


class Network(AbstractNetwork):
    """ FreeBSD implementation of AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ifconfig"]

    def dev(self, options=None):
        def check(dev):
            out = run(self._LOCAL_IP_CMD + [dev])
            if not out:
                return False
            return active.search(out)

        active = re.compile(r"^\s+status: (associated|active)$", re.M)
        dev_list = run(self._LOCAL_IP_CMD + ["-l"])
        if dev_list is None:
            LOG.debug("unable to get network devices")
            return None

        dev_list = dev_list.split()
        return next(filter(check, dev_list), None)

    def _ssid(self):
        ssid_cmd = tuple(self._LOCAL_IP_CMD + [self.dev()])
        ssid_reg = re.compile(r"ssid (.*) channel")
        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        cmd = ["netstat", "-nbiI", dev]
        if mode == "up":
            col = 10
        else:
            col = 7

        out = run(cmd)
        if not out:
            return 0

        out = out.strip().splitlines()
        line = out[1]
        line = line.split()
        return int(line[col])


class Misc(AbstractMisc):
    """ FreeBSD implementation of AbstractMisc class """

    def _vol(self):
        """ Stub """
        return None

    def _scr(self):
        """ Stub """
        return None, None


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
