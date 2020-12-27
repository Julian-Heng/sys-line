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

""" Linux specific module """

import re
import shlex
import shutil

from abc import abstractmethod
from functools import lru_cache
from pathlib import Path as p

from . import wm
from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc, BatteryStub)
from ..tools.utils import open_read, run, percent, round_trim


class Cpu(AbstractCpu):
    """ A Linux implementation of the AbstractCpu class """

    FILES = {
        "proc_cpu": "/proc/cpuinfo",
        "sys_cpu": "/sys/devices/system/cpu",
        "proc_load": "/proc/loadavg",
        "sys_platform": "/sys/devices/platform",
        "sys_hwmon": "/sys/class/hwmon",
        "proc_uptime": "/proc/uptime",
    }

    @property
    @lru_cache(maxsize=1)
    def cpu_file(self):
        """ Returns cached /proc/cpuinfo """
        return open_read(Cpu.FILES["proc_cpu"])

    @property
    @lru_cache(maxsize=1)
    def cores(self):
        return len(re.findall(r"^processor", self.cpu_file, re.M))

    def _cpu_speed(self):
        def check(_file):
            return speed_reg.search(str(_file))

        speed_reg = re.compile(r"(bios_limit|(scaling|cpuinfo)_max_freq)$")
        cpu = re.search(r"model name\s+: (.*)", self.cpu_file, re.M).group(1)

        speed_dir = Cpu.FILES["sys_cpu"]
        speed = next((f for f in p(speed_dir).rglob("*") if check(f)), None)

        if speed is not None:
            speed = float(open_read(speed))
            speed = round_trim(speed / 1e6, 2)

        return cpu, speed

    def _load_avg(self):
        return open_read(Cpu.FILES["proc_load"]).split(" ")[:3]

    @property
    def fan(self):
        fan = None
        fan_dir = Cpu.FILES["sys_platform"]
        glob = "fan1_input"
        files = (f for f in p(fan_dir).rglob(glob))

        fan = next(files, None)
        if fan is not None:
            fan = int(open_read(fan).strip())

        return fan

    @property
    def temp(self):
        def check(_file):
            return p(_file).exists() and "temp" in open_read(_file)

        def glob(_dir):
            return p(_dir).glob("*")

        temp = None
        files = (f for f in glob(Cpu.FILES["sys_hwmon"])
                 if check(f"{f}/name"))

        temp_dir = next(files, None)
        if temp_dir is not None:
            files = sorted(p(temp_dir).glob("temp*_input"))
            if files:
                temp = float(open_read(str(files[0]))) / 1000

        return temp

    def _uptime(self):
        uptime = open_read(Cpu.FILES["proc_uptime"]).strip().split(" ")[0]
        return int(float(uptime))


@lru_cache(maxsize=1)
def _mem_file():
    """ Returns cached /proc/meminfo """
    reg = re.compile(r"\s+|kB")
    mem_file = open_read("/proc/meminfo").strip().split("\n")
    mem_file = dict(reg.sub("", i).split(":", 1) for i in mem_file)
    mem_file = {k: int(v) for k, v in mem_file.items()}
    return mem_file


class Memory(AbstractMemory):
    """ A Linux implementation of the AbstractMemory class """

    def _used(self):
        mem_file = _mem_file()
        keys = [["MemTotal", "Shmem"],
                ["MemFree", "Buffers", "Cached", "SReclaimable"]]
        used = sum([mem_file[i] for i in keys[0]])
        used -= sum([mem_file[i] for i in keys[1]])
        return used, "KiB"

    def _total(self):
        return _mem_file()["MemTotal"], "KiB"


class Swap(AbstractSwap):
    """ A self implementation of the AbstractSwap class """

    def _used(self):
        mem_file = _mem_file()
        used = mem_file["SwapTotal"] - mem_file["SwapFree"]
        return used, "KiB"

    def _total(self):
        return _mem_file()["SwapTotal"], "KiB"


class Disk(AbstractDisk):
    """ A Linux implementation of the AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P"]

    @property
    @lru_cache(maxsize=1)
    def lsblk_entries(self):
        """
        Returns the output of lsblk in a dictionary with devices as keys
        """
        lsblk_entries = None
        lsblk_out = None
        if shutil.which("lsblk"):
            columns = ["NAME", "LABEL", "PARTLABEL", "FSTYPE"]
            cmd = ["lsblk", "--output", ",".join(columns), "--paths",
                   "--pairs"]
            lsblk_out = run(cmd).strip().split("\n")

        if lsblk_out is not None and lsblk_out:
            lsblk_entries = dict()
            for line in lsblk_out:
                out = shlex.split(line)
                out = dict(re.sub("\"", "", i).split("=", 1) for i in out)
                lsblk_entries[out["NAME"]] = out

        return lsblk_entries

    @property
    def name(self):
        labels = ["LABEL", "PARTLABEL"]
        lsblk_entries = self.lsblk_entries
        names = {k: None for k in self.original_dev}

        if lsblk_entries is not None:
            names = {k: next((v[i] for i in labels if v[i]), None)
                     for k, v in self.lsblk_entries.items()
                     if k in self.original_dev}

        return names

    @property
    def partition(self):
        lsblk_entries = self.lsblk_entries
        partitions = {k: None for k in self.original_dev}

        if lsblk_entries is not None:
            partitions = {k: v["FSTYPE"]
                          for k, v in self.lsblk_entries.items()
                          if k in self.original_dev}

        return partitions


class Battery(AbstractBattery):
    """ A Linux implementation of the AbstractBattery class """

    @property
    @abstractmethod
    def current(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def full(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def drain(self):
        """ Abstract current class to be implemented """

    @property
    @lru_cache(maxsize=1)
    def status(self):
        """ Returns cached battery status file """
        return open_read(f"{Linux.bat_dir()}/status").strip()

    @property
    @lru_cache(maxsize=1)
    def current_charge(self):
        """ Returns cached battery current charge file """
        current = self.current
        return None if Linux.bat_dir() is None else int(open_read(current))

    @property
    @lru_cache(maxsize=1)
    def full_charge(self):
        """ Returns cached battery full charge file """
        return None if Linux.bat_dir() is None else int(open_read(self.full))

    @property
    @lru_cache(maxsize=1)
    def drain_rate(self):
        """ Returns cached battery drain rate file """
        return None if Linux.bat_dir() is None else int(open_read(self.drain))

    @lru_cache(maxsize=1)
    def _compare_status(self, query):
        """ Compares status to query """
        return None if Linux.bat_dir() is None else self.status == query

    @property
    def is_present(self):
        return Linux.bat_dir() is not None

    @property
    def is_charging(self):
        return self._compare_status("Charging")

    @property
    def is_full(self):
        return self._compare_status("Full")

    @property
    def percent(self):
        perc = None
        if Linux.bat_dir() is not None:
            current_charge = self.current_charge
            full_charge = self.full_charge

            perc = percent(current_charge, full_charge)
            perc = round_trim(perc, self.options.percent_round)

        return perc

    def _time(self):
        remaining = 0
        if Linux.bat_dir() is not None and self.drain_rate:
            charge = self.current_charge
            if self.is_charging:
                charge = self.full_charge - charge
            remaining = int((charge / self.drain_rate) * 3600)

        return remaining

    @property
    def power(self):
        pass


class BatteryAmp(Battery):
    """ Sub-Battery class for systems that stores battery info in amps """

    @property
    @lru_cache(maxsize=1)
    def current(self):
        """ Returns current charge filename """
        return f"{Linux.bat_dir()}/charge_now"

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full charge filename """
        return f"{Linux.bat_dir()}/charge_full"

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns current filename """
        return f"{Linux.bat_dir()}/current_now"

    @property
    def power(self):
        power = None
        if Linux.bat_dir() is not None:
            voltage = int(open_read(f"{Linux.bat_dir()}/voltage_now"))
            power = (self.drain_rate * voltage) / 1e12
            power = round_trim(power, self.options.power_round)

        return power


class BatteryWatt(Battery):
    """ Sub-Battery class for systems that stores battery info in watt """

    @property
    @lru_cache(maxsize=1)
    def current(self):
        """ Returns current energy filename """
        return f"{Linux.bat_dir()}/energy_now"

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full energy filename """
        return f"{Linux.bat_dir()}/energy_full"

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns power filename """
        return f"{Linux.bat_dir()}/power_now"

    @property
    def power(self):
        return round_trim(self.drain_rate / 1e6, self.options.power_round)


class Network(AbstractNetwork):
    """ A Linux implementation of the AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ip", "address", "show", "dev"]

    @property
    def dev(self):
        def check(_file):
            return open_read(f"{_file}/operstate").strip() == "up"

        def find(_dir):
            return p(_dir).glob("[!v]*")

        return next((f.name for f in find(Linux.FILES["sys_net"])
                     if check(f)), None)

    def _ssid(self):
        ssid_cmd = None
        ssid_reg = None
        dev = self.dev

        if dev is not None:
            try:
                wifi_path = Linux.FILES["proc_wifi"]
                wifi_out = open_read(wifi_path).strip().split("\n")
                if len(wifi_out) >= 3 and shutil.which("iw"):
                    ssid_cmd = ("iw", "dev", dev, "link")
                    ssid_reg = re.compile(r"^SSID: (.*)$")
            except FileNotFoundError:
                ssid_cmd = None
                ssid_reg = None

        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        net = Linux.FILES["sys_net"]
        mode = "tx" if mode == "up" else "rx"
        stat_file = f"{net}/{dev}/statistics/{mode}_bytes"
        return int(open_read(stat_file))


class Misc(AbstractMisc):
    """ A Linux implementation of the AbstractMisc class """

    @property
    def vol(self):
        def check(_dir):
            return _dir.is_dir() and _dir.name.isdigit()

        def extract(_file):
            return open_read(f"{_file}/cmdline")

        systems = {"pulseaudio": Linux.vol_pulseaudio}

        reg = re.compile(r"|".join(systems.keys()))

        vol = None
        pids = (extract(i) for i in p("/proc").iterdir() if check(i))
        audio = next((reg.search(i) for i in pids if i and reg.search(i)),
                     None)

        if audio is not None:
            try:
                vol = systems[audio.group(0)]()
                if vol is not None:
                    vol = round_trim(vol, self.options.volume_round)
            except KeyError:
                vol = None

        return vol

    @property
    def scr(self):
        def check(_file):
            return "kbd" not in _file and "backlight" in _file

        scr = None
        backlight_path = p(Linux.FILES["sys_backlight"])

        if backlight_path.exists():
            scr_files = (f for f in backlight_path.rglob("*") if check(f.name))
            scr_dir = next(scr_files, None)

            if scr_dir is not None:
                curr = int(open_read(f"{scr_dir}/brightness"))
                max_scr = int(open_read(f"{scr_dir}/max_brightness"))
                scr = percent(curr, max_scr)
                scr = round_trim(scr, self.options.screen_round)

        return scr


class Linux(System):
    """ A Linux implementation of the abstract System class """

    FILES = {
        # Mem/Swap
        "proc_mem": "/proc/meminfo",

        # Battery
        "sys_power_supply": "/sys/class/power_supply",

        # Network
        "sys_net": "/sys/class/net",
        "proc_wifi": "/proc/net/wireless",

        # Misc
        "sys_backlight": "/sys/devices/backlight"
    }

    def __init__(self, options):
        super(Linux, self).__init__(options,
                                    cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                    bat=Linux.detect_battery(), net=Network,
                                    wm=self.detect_window_manager(),
                                    misc=Misc)

    @staticmethod
    @lru_cache(maxsize=1)
    def bat_dir():
        """ Returns the path for the battery directory """
        def check(_file):
            return p(_file).exists() and bool(int(open_read(_file)))

        _bat_dir = p(Linux.FILES["sys_power_supply"]).glob("*BAT*")
        _bat_dir = (d for d in _bat_dir if check(f"{d}/present"))
        return next(_bat_dir, None)

    @staticmethod
    @lru_cache(maxsize=1)
    def detect_battery():
        """
        Linux stores battery information in /sys/class/power_supply However,
        depending on the machine/driver it may store different information.

        Example:

            On one machine it might contain these files:
                /sys/class/power_supply/charge_now
                /sys/class/power_supply/charge_full
                /sys/class/power_supply/current_now

            On another it might contain these files:
                /sys/class/power_supply/energy_now
                /sys/class/power_supply/energy_full
                /sys/class/power_supply/power_now

        So the purpose of this method is to determine which implementation it
        should use
        """
        avail = {
            f"{Linux.bat_dir()}/charge_now": BatteryAmp,
            f"{Linux.bat_dir()}/energy_now": BatteryWatt
        }

        return next((v for k, v in avail.items() if p(k).exists()),
                    BatteryStub)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "Xorg": wm.Xorg,
        }

    @staticmethod
    @lru_cache(maxsize=1)
    def vol_pulseaudio():
        """ Return system volume using pulse audio """
        default_reg = re.compile(r"^set-default-sink (.*)$", re.M)
        pac_dump = run(["pacmd", "dump"])

        vol = None
        default = default_reg.search(pac_dump)
        if default is not None:
            vol_reg = fr"^set-sink-volume {default.group(1)} 0x(.*)$"
            vol_reg = re.compile(vol_reg, re.M)
            vol = vol_reg.search(pac_dump)
            if vol is not None:
                vol = percent(int(vol.group(1), 16), 0x10000)

        return vol
