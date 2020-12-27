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

""" Darwin specific module """

import plistlib
import re
import shutil
import time

from functools import lru_cache

from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from .wm import Yabai
from ..tools.sysctl import Sysctl
from ..tools.utils import percent, run, round_trim


class Cpu(AbstractCpu):
    """ Darwin implementation of AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def cores(self):
        return int(Sysctl.query("hw.logicalcpu_max"))

    def _cpu_string(self):
        return Sysctl.query("machdep.cpu.brand_string")

    def _cpu_speed(self):
        return None

    def _load_avg(self):
        return Sysctl.query("vm.loadavg").split()[1:4]

    @property
    def fan(self):
        fan = None
        if shutil.which("osx-cpu-temp"):
            regex = r"(\d+) RPM"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            fan = int(match.group(1)) if match else None

        return fan

    @property
    def temp(self):
        temp = None
        if shutil.which("osx-cpu-temp"):
            regex = r"CPU: ((\d+\.)?\d+)"
            match = re.search(regex, run(["osx-cpu-temp", "-f", "-c"]))
            temp = float(match.group(1)) if match else 0.0
            temp = round_trim(temp, self.options.temp_round)

        return temp

    def _uptime(self):
        reg = re.compile(r"sec = (\d+),")
        sec = reg.search(Sysctl.query("kern.boottime")).group(1)
        sec = int(time.time()) - int(sec)

        return sec


class Memory(AbstractMemory):
    """ Darwin implementation of AbstractMemory class """

    def _used(self):
        words = ["active", "wired down", "occupied by compressor"]
        vm_stat = run(["vm_stat"]).strip().split("\n")[1:]
        vm_stat = (re.sub(r"Pages |\.", r"", i) for i in vm_stat)
        vm_stat = dict(i.split(":", 1) for i in vm_stat)
        value = sum([int(vm_stat[i]) for i in words]) * 4096
        return value, "B"

    def _total(self):
        return int(Sysctl.query("hw.memsize")), "B"


class Swap(AbstractSwap):
    """ Darwin implementation of AbstractSwap class """

    @property
    @lru_cache(maxsize=1)
    def swapusage(self):
        """ Returns swapusage from sysctl """
        return Sysctl.query("vm.swapusage").strip()

    def _lookup_swap(self, search):
        value = 0

        regex = fr"{search} = (\d+\.\d+)M"
        match = re.search(regex, self.swapusage)

        if match:
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
    def diskutil(self):
        """ Returns diskutil program output as a dict """
        devs = self.original_dev.values()
        cmd = ["diskutil", "info", "-plist"]
        diskutil = None
        if devs is not None:
            out = {dev: run(cmd + [dev]).encode("utf-8") for dev in devs}
            diskutil = {k: plistlib.loads(v) for k, v in out.items()}

        return diskutil

    def _lookup_diskutil(self, key):
        try:
            return {k: v[key] for k, v in self.diskutil.items()}
        except KeyError:
            return None

    @property
    def name(self):
        return self._lookup_diskutil("VolumeName")

    @property
    def partition(self):
        return self._lookup_diskutil("FilesystemName")


class Battery(AbstractBattery):
    """ Darwin implementation of AbstractBattery class """

    @property
    @lru_cache(maxsize=1)
    def bat(self):
        """ Returns battery info from ioreg as a dict """
        bat = run(["ioreg", "-rc", "AppleSmartBattery"]).split("\n")[1:]
        bat = (re.sub("[\"{}]", "", i.strip()) for i in bat)
        bat = dict(i.split(" = ", 1) for i in bat if i.strip())
        return bat if bat else None

    @lru_cache(maxsize=1)
    def _current(self):
        current = 0
        if self.is_present:
            current = int(self.bat["InstantAmperage"])

            # Fix current if it underflows in ioreg
            current -= pow(2, 64) if len(str(current)) >= 20 else 0
            current = abs(current)

        return current

    @lru_cache(maxsize=1)
    def _current_capacity(self):
        return int(self.bat["CurrentCapacity"]) if self.is_present else None

    @property
    @lru_cache(maxsize=1)
    def is_present(self):
        is_present = False
        if self.bat is not None:
            is_present = self.bat["BatteryInstalled"] == "Yes"
        return is_present

    @property
    def is_charging(self):
        return self.bat["IsCharging"] == "Yes" if self.is_present else None

    @property
    def is_full(self):
        return self.bat["FullyCharged"] == "Yes" if self.is_present else None

    @property
    def percent(self):
        perc = None

        if self.is_present:
            current_capacity = self._current_capacity()
            max_capacity = int(self.bat["MaxCapacity"])
            perc = percent(current_capacity, max_capacity)
            perc = round_trim(perc, self.options.percent_round)

        return perc

    def _time(self):
        charge = 0

        if self.is_present and self._current() != 0:
            charge = self._current_capacity()
            if self.is_charging:
                charge = int(self.bat["MaxCapacity"]) - charge
            charge = int((charge / self._current()) * 3600)

        return charge

    @property
    def power(self):
        power = None

        if self.is_present:
            voltage = int(self.bat["Voltage"])
            power = (self._current() * voltage) / 1e6
            power = round_trim(power, self.options.power_round)

        return power


class Network(AbstractNetwork):
    """ Darwin implementation of AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ifconfig"]

    @property
    def dev(self):
        def check(dev):
            return active.search(run(self._LOCAL_IP_CMD + [dev]))

        active = re.compile(r"status: active")
        dev_reg = re.compile(r"Device: (.*)$")

        dev_list = run(["networksetup", "-listallhardwareports"])
        dev_list = dev_list.strip().split("\n")
        dev_list = (dev_reg.search(i) for i in dev_list)
        dev_list = (i.group(1) for i in dev_list if i)

        return next((i for i in dev_list if check(i)), None)

    def _ssid(self):
        ssid_cmd_path = ["System", "Library", "PrivateFrameworks",
                         "Apple80211.framework", "Versions", "Current",
                         "Resources", "airport"]
        ssid_cmd = ("/{}".format("/".join(ssid_cmd_path)), "--getinfo")
        ssid_reg = re.compile(r"^SSID: (.*)$")

        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        cmd = ["netstat", "-nbiI", dev]
        reg_str = r"^({})(\s+[^\s]+){{{}}}\s+(\d+)"
        reg_str = reg_str.format(dev, 8 if mode == "up" else 5)
        reg = re.compile(reg_str)
        match = (reg.match(line) for line in run(cmd).split("\n"))

        return next((int(i.group(3)) for i in match if i), 0)


class Misc(AbstractMisc):
    """ Darwin implementation of AbstractMisc class """

    @property
    def vol(self):
        cmd = ["vol"]
        osa = ["osascript", "-e", "output volume of (get volume settings)"]
        vol = float(run(cmd if shutil.which("vol") else osa))
        return round_trim(vol, self.options.volume_round)

    @property
    def scr(self):
        def check(line):
            return "IODisplayParameters" in line

        scr = None
        scr_out = run(["ioreg", "-rc", "AppleBacklightDisplay"]).split("\n")
        scr_out = next((i for i in scr_out if check(i)), None)
        if scr_out is not None:
            reg = r"\"brightness\"=[^\=]+=(\d+),[^,]+,[^\=]+=(\d+)"
            scr = re.search(reg, scr_out)
            if int(scr.group(1)) == 0:
                reg = r"\"brightness\"=[^,]+=[^\=]+=(\d+),[^\=]+=(\d+)"
                scr = re.search(reg, scr_out)
            scr = percent(int(scr.group(2)), int(scr.group(1)))
            scr = round_trim(scr, self.options.screen_round)

        return scr


class Darwin(System):
    """ A Darwin implementation of the abstract System class """

    def __init__(self, options):
        super(Darwin, self).__init__(options,
                                     cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                     bat=Battery, net=Network,
                                     wm=self.detect_window_manager(),
                                     misc=Misc)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "yabai": Yabai,
        }
