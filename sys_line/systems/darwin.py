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
#
# pylint: disable=no-self-use

""" Darwin specific module """

import plistlib
import re
import shutil
import time

from functools import lru_cache
from pathlib import Path

from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from .wm import Yabai
from ..tools.sysctl import Sysctl
from ..tools.utils import run


class Cpu(AbstractCpu):
    """ Darwin implementation of AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def _osx_cpu_temp_exe(self):
        """ Returns the path to the osx-cpu-temp executable """
        return shutil.which("osx-cpu-temp")

    def cores(self, options=None):
        return int(Sysctl.query("hw.logicalcpu_max"))

    def _cpu_string(self):
        return Sysctl.query("machdep.cpu.brand_string")

    def _cpu_speed(self):
        return None

    def _load_avg(self):
        query = Sysctl.query("vm.loadavg")
        if query is None:
            return None

        return query.split()[1:4]

    def fan(self, options=None):
        if not self._osx_cpu_temp_exe:
            return None

        regex = r"(\d+) RPM"
        out = run([self._osx_cpu_temp_exe, "-f", "-c"])

        if out is None:
            return None

        match = re.search(regex, out)
        if not match:
            return None

        return int(match.group(1))

    def _temp(self):
        if not self._osx_cpu_temp_exe:
            return None

        regex = r"CPU: ((\d+\.)?\d+)"
        out = run([self._osx_cpu_temp_exe, "-f", "-c"])

        if out is None:
            return None

        match = re.search(regex, out)
        if not match:
            return None

        return float(match.group(1))

    def _uptime(self):
        reg = re.compile(r"sec = (\d+),")
        query = Sysctl.query("kern.boottime")
        if query is None:
            return 0

        sec = reg.search(query).group(1)
        sec = int(time.time()) - int(sec)
        return sec


class Memory(AbstractMemory):
    """ Darwin implementation of AbstractMemory class """

    def _used(self):
        words = ["active", "wired down", "occupied by compressor"]
        vm_stat = run(["vm_stat"])

        if vm_stat is None:
            return None, None

        vm_stat = vm_stat.strip().splitlines()[1:]
        vm_stat = (re.sub(r"Pages |\.", r"", i) for i in vm_stat)
        vm_stat = dict(i.split(":", 1) for i in vm_stat)
        used = sum(int(vm_stat.get(i, 0)) for i in words) * 4096
        return used, "B"

    def _total(self):
        total = int(Sysctl.query("hw.memsize", default=0))
        return total, "B"


class Swap(AbstractSwap):
    """ Darwin implementation of AbstractSwap class """

    @property
    @lru_cache(maxsize=1)
    def _swapusage(self):
        """ Returns swapusage from sysctl """
        swapusage = Sysctl.query("vm.swapusage", default="").strip()
        return swapusage

    def _lookup_swap(self, search):
        value = 0

        regex = fr"{search} = (\d+\.\d+)M"
        match = re.search(regex, self._swapusage)

        if not match:
            return 0

        value = int(float(match.group(1)) * pow(1024, 2))
        return value

    def _used(self):
        return self._lookup_swap("used"), "B"

    def _total(self):
        return self._lookup_swap("total"), "B"


class Disk(AbstractDisk):
    """ Darwin implementation of AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P", "-k"]

    @property
    @lru_cache(maxsize=1)
    def _diskutil(self):
        """ Returns diskutil program output as a dict """
        devs = self._original_dev().values()
        cmd = ["diskutil", "info", "-plist"]
        if devs is None:
            return None

        out = {dev: run(cmd + [dev]).encode("utf-8") for dev in devs}
        diskutil = {k: plistlib.loads(v) for k, v in out.items()}
        return diskutil

    def _lookup_diskutil(self, key):
        diskutil = self._diskutil
        return {k: v.get(key, None) for k, v in diskutil.items()}

    def name(self, options=None):
        return self._lookup_diskutil("VolumeName")

    def partition(self, options=None):
        return self._lookup_diskutil("FilesystemName")


class Battery(AbstractBattery):
    """ Darwin implementation of AbstractBattery class """

    @lru_cache(maxsize=1)
    def _current(self):
        current = 0
        is_present = self.is_present()
        if not is_present:
            return 0

        ioreg = Battery.ioreg()
        current = int(ioreg.get("InstantAmperage", 0))

        # Fix current if it underflows in ioreg
        if len(str(current)) >= 20:
            current -= pow(2, 64)

        current = abs(current)
        return current

    @lru_cache(maxsize=1)
    def _current_capacity(self):
        is_present = self.is_present()
        if not is_present:
            return None

        ioreg = Battery.ioreg()
        if ioreg is None or "CurrentCapacity" not in ioreg:
            return None

        return int(ioreg["CurrentCapacity"])

    def is_present(self, options=None):
        ioreg = Battery.ioreg()
        if ioreg is None:
            return False

        is_present = ioreg.get("BatteryInstalled", "") == "Yes"
        return is_present

    def is_charging(self, options=None):
        is_present = self.is_present()
        if not is_present:
            return None

        ioreg = Battery.ioreg()
        is_charging = ioreg.get("IsCharging", "") == "Yes"
        return is_charging

    def is_full(self, options=None):
        is_present = self.is_present()
        if not is_present:
            return None

        ioreg = Battery.ioreg()
        is_charging = ioreg.get("FullyCharged", "") == "Yes"
        return is_charging

    def _percent(self):
        current_capacity = self._current_capacity()
        ioreg = Battery.ioreg()

        if ioreg is None:
            max_capacity = 0
        else:
            max_capacity = int(ioreg.get("MaxCapacity", 0))

        return current_capacity, max_capacity

    def _time(self):
        charge = 0

        is_present = self.is_present()
        current = self._current()
        if not is_present or current == 0:
            return 0

        charge = self._current_capacity()
        is_charging = self.is_charging()

        if is_charging:
            ioreg = Battery.ioreg()
            if ioreg is None:
                return 0

            charge = int(ioreg.get("MaxCapacity", 0)) - charge

        charge = int((charge / self._current()) * 3600)
        return charge

    def _power(self):
        power = None

        is_present = self.is_present()
        if not is_present:
            return None

        ioreg = Battery.ioreg()
        if ioreg is None:
            return None

        voltage = int(ioreg.get("Voltage", 0))
        power = (self._current() * voltage) / 1e6
        return power

    @staticmethod
    @lru_cache(maxsize=1)
    def ioreg():
        """ Returns battery info from ioreg as a dict """
        bat = run(["ioreg", "-rc", "AppleSmartBattery"])
        if bat is None:
            return None

        bat = bat.splitlines()[1:]
        bat = (re.sub("[\"{}]", "", i.strip()) for i in bat)
        bat = dict(i.split(" = ", 1) for i in bat if i.strip())
        if not bat:
            return None

        return bat


class Network(AbstractNetwork):
    """ Darwin implementation of AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ifconfig"]

    def dev(self, options=None):
        def check(dev):
            return active.search(run(self._LOCAL_IP_CMD + [dev]))

        active = re.compile(r"status: active")
        dev_reg = re.compile(r"Device: (.*)$")

        dev_list = run(["networksetup", "-listallhardwareports"])
        if dev_list is None:
            return None

        dev_list = dev_list.strip().splitlines()
        dev_list = map(dev_reg.search, dev_list)
        dev_list = (i.group(1) for i in dev_list if i)

        dev = next(filter(check, dev_list), None)
        return dev

    def _ssid(self):
        ssid_cmd_path = Path("/", "System", "Library", "PrivateFrameworks",
                             "Apple80211.framework", "Versions", "Current",
                             "Resources", "airport")
        ssid_cmd = (ssid_cmd_path.resolve(), "--getinfo")
        ssid_reg = re.compile(r"^SSID: (.*)$")

        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        cmd = ["netstat", "-nbiI", dev]
        reg = r"^({})(\s+[^\s]+){{{}}}\s+(\d+)"

        if mode == "up":
            col = 8
        else:
            col = 5

        reg = reg.format(dev, col)
        reg = re.compile(reg)
        match = (reg.match(line) for line in run(cmd).splitlines())

        delta = next((int(i.group(3)) for i in match if i), 0)
        return delta


class Misc(AbstractMisc):
    """ Darwin implementation of AbstractMisc class """

    @property
    @lru_cache(maxsize=1)
    def _vol_exe(self):
        """ Returns the path to the darwin-vol executable """
        return shutil.which("vol")

    def _vol(self):
        vol = None
        if self._vol_exe:
            out = run([self._vol_exe])
        else:
            cmd = ["osascript", "-e", "output volume of (get volume settings)"]
            out = run(cmd)

        if out is None:
            return None

        vol = float(out)
        return vol

    def _scr(self):
        def check(line):
            return "IODisplayParameters" in line

        scr_out = run(["ioreg", "-rc", "AppleBacklightDisplay"])
        if scr_out is None:
            return None, None

        scr_out = scr_out.splitlines()
        scr_out = next(filter(check, scr_out), None)
        if scr_out is None:
            return None, None

        reg = r"\"brightness\"=[^\=]+=(\d+),[^,]+,[^\=]+=(\d+)"
        scr = re.search(reg, scr_out)
        if int(scr.group(1)) == 0:
            reg = r"\"brightness\"=[^,]+=[^\=]+=(\d+),[^\=]+=(\d+)"
            scr = re.search(reg, scr_out)

        current_scr = int(scr.group(2))
        max_scr = int(scr.group(1))

        return current_scr, max_scr


class Darwin(System):
    """ A Darwin implementation of the abstract System class """

    def __init__(self, default_options):
        super(Darwin, self).__init__(default_options,
                                     cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                     bat=Battery, net=Network,
                                     wm=self.detect_window_manager(),
                                     misc=Misc)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "yabai": Yabai,
        }
