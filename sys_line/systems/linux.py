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
from pathlib import Path

from . import wm
from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc, BatteryStub)
from ..tools.utils import open_read, run, percent, round_trim


class Cpu(AbstractCpu):
    """ A Linux implementation of the AbstractCpu class """

    FILES = {
        "proc_cpu": Path("/proc/cpuinfo"),
        "sys_cpu": Path("/sys/devices/system/cpu"),
        "proc_load": Path("/proc/loadavg"),
        "sys_platform": Path("/sys/devices/platform"),
        "sys_hwmon": Path("/sys/class/hwmon"),
        "proc_uptime": Path("/proc/uptime"),
    }

    @property
    @lru_cache(maxsize=1)
    def _cpu_file(self):
        """ Returns cached /proc/cpuinfo """
        return open_read(Cpu.FILES["proc_cpu"])

    @property
    @lru_cache(maxsize=1)
    def _cpu_speed_file_path(self):
        speed_reg = re.compile(r"(bios_limit|(scaling|cpuinfo)_max_freq)$")
        speed_dir = Cpu.FILES["sys_cpu"]
        path = (f for f in speed_dir.rglob("*") if speed_reg.search(str(f)))
        return next(path, None)

    @property
    @lru_cache(maxsize=1)
    def _cpu_temp_file_paths(self):
        def check(_file):
            return _file.exists() and "temp" in open_read(_file)

        temp_files = None
        temp_dir_base = Cpu.FILES["sys_hwmon"]
        files = (f for f in temp_dir_base.glob("*")
                 if check(f.joinpath("name")))

        temp_dir = next(files, None)
        if temp_dir is not None:
            temp_files = sorted(temp_dir.glob("temp*_input"))

        return temp_files

    @property
    @lru_cache(maxsize=1)
    def _cpu_fan_file_path(self):
        files = (f for f in Cpu.FILES["sys_platform"].rglob("fan1_input"))
        return next(files, None)

    @property
    @lru_cache(maxsize=1)
    def cores(self):
        return len(re.findall(r"^processor", self._cpu_file, re.M))

    def _cpu_string(self):
        cpu = None
        match = re.search(r"model name\s+: (.*)", self._cpu_file, re.M)
        if match is not None:
            cpu = match.group(1)
        return cpu

    def _cpu_speed(self):
        speed = None
        speed_file = self._cpu_speed_file_path
        if speed_file is not None:
            speed = round_trim(float(open_read(speed_file)) / 1e6, 2)
        return speed

    def _load_avg(self):
        load = None
        load_file = open_read(Cpu.FILES["proc_load"])
        if load_file is not None:
            load = load_file.split(" ")[:3]
        return load

    @property
    def fan(self):
        fan = None
        fan_file = self._cpu_fan_file_path
        if fan_file is not None:
            fan = int(open_read(fan_file).strip())
        return fan

    def _temp(self):
        temp = None
        temp_files = self._cpu_temp_file_paths
        if temp_files:
            temp = float(open_read(str(next(iter(temp_files))))) / 1000
        return temp

    def _uptime(self):
        uptime = None
        uptime_file = open_read(Cpu.FILES["proc_uptime"])
        if uptime_file is not None:
            uptime = int(float(uptime_file.strip().split(" ")[0]))
        return uptime


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
        used = sum(mem_file[i] for i in keys[0])
        used -= sum(mem_file[i] for i in keys[1])
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
    def _lsblk_entries(self):
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
        lsblk_entries = self._lsblk_entries
        names = {k: None for k in self.original_dev}

        if lsblk_entries is not None:
            names = {k: next((v[i] for i in labels if v[i]), None)
                     for k, v in self._lsblk_entries.items()
                     if k in self.original_dev}

        return names

    @property
    def partition(self):
        lsblk_entries = self._lsblk_entries
        partitions = {k: None for k in self.original_dev}

        if lsblk_entries is not None:
            partitions = {k: v["FSTYPE"]
                          for k, v in self._lsblk_entries.items()
                          if k in self.original_dev}

        return partitions


class Battery(AbstractBattery):
    """ A Linux implementation of the AbstractBattery class """

    FILES = {
        "sys_power_supply": Path("/sys/class/power_supply"),
    }

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
        return open_read(Battery.directory().joinpath("status")).strip()

    @property
    @lru_cache(maxsize=1)
    def current_charge(self):
        """ Returns cached battery current charge file """
        bat_dir = Battery.directory()
        if bat_dir is not None:
            return int(open_read(bat_dir.joinpath(self.current)))
        return None

    @property
    @lru_cache(maxsize=1)
    def full_charge(self):
        """ Returns cached battery full charge file """
        bat_dir = Battery.directory()
        if bat_dir is not None:
            return int(open_read(bat_dir.joinpath(self.full)))
        return None

    @property
    @lru_cache(maxsize=1)
    def drain_rate(self):
        """ Returns cached battery drain rate file """
        bat_dir = Battery.directory()
        if bat_dir is not None:
            return int(open_read(bat_dir.joinpath(self.drain)))
        return None

    @lru_cache(maxsize=1)
    def _compare_status(self, query):
        """ Compares status to query """
        bat_dir = Battery.directory()
        if bat_dir is not None:
            return self.status == query
        return None

    @property
    def is_present(self):
        return Battery.directory() is not None

    @property
    def is_charging(self):
        return self._compare_status("Charging")

    @property
    def is_full(self):
        return self._compare_status("Full")

    def _percent(self):
        return self.current_charge, self.full_charge

    def _time(self):
        remaining = 0
        if self.is_present and self.drain_rate:
            charge = self.current_charge
            if self.is_charging:
                charge = self.full_charge - charge
            remaining = int((charge / self.drain_rate) * 3600)

        return remaining

    def _power(self):
        pass

    @staticmethod
    @lru_cache(maxsize=1)
    def directory():
        """ Returns the path for the battery directory """
        def check(_file):
            return _file.exists() and bool(int(open_read(_file)))

        _dir = Battery.FILES["sys_power_supply"].glob("*BAT*")
        _dir = (d for d in _dir if check(d.joinpath("present")))
        return next(_dir, None)

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
        bat_dir = Battery.directory()
        if bat_dir is None:
            return BatteryStub

        avail = {
            bat_dir.joinpath("charge_now"): BatteryAmp,
            bat_dir.joinpath("energy_now"): BatteryWatt,
        }

        return next((v for k, v in avail.items() if k.exists()),
                    BatteryStub)


class BatteryAmp(Battery):
    """ Sub-Battery class for systems that stores battery info in amps """

    @property
    @lru_cache(maxsize=1)
    def current(self):
        """ Returns current charge filename """
        return "charge_now"

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full charge filename """
        return "charge_full"

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns current filename """
        return "current_now"

    def _power(self):
        power = None
        bat_dir = Battery.directory()
        if bat_dir is not None:
            voltage_path = bat_dir.joinpath("voltage_now")
            voltage = int(open_read(voltage_path))
            power = (self.drain_rate * voltage) / 1e12

        return power


class BatteryWatt(Battery):
    """ Sub-Battery class for systems that stores battery info in watt """

    @property
    @lru_cache(maxsize=1)
    def current(self):
        """ Returns current energy filename """
        return "energy_now"

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full energy filename """
        return "energy_full"

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns power filename """
        return "power_now"

    def _power(self):
        return self.drain_rate / 1e6


class Network(AbstractNetwork):
    """ A Linux implementation of the AbstractNetwork class """

    FILES = {
        "sys_net": Path("/sys/class/net"),
        "proc_wifi": Path("/proc/net/wireless"),
    }

    @property
    def _LOCAL_IP_CMD(self):
        return ["ip", "address", "show", "dev"]

    @property
    def dev(self):
        # Skip virtual network devices
        files = Network.FILES["sys_net"].glob("[!v]*")
        return next((f.name for f in files
                     if "up" in open_read(f.joinpath("operstate"))), None)

    def _ssid(self):
        ssid_cmd = None
        ssid_reg = None
        dev = self.dev

        if dev is not None:
            wifi_path = Network.FILES["proc_wifi"]
            wifi_out = open_read(wifi_path)
            if wifi_out is not None:
                wifi_out = wifi_out.strip().splitlines()
                if len(wifi_out) >= 3 and shutil.which("iw"):
                    ssid_cmd = ("iw", "dev", dev, "link")
                    ssid_reg = re.compile(r"^SSID: (.*)$")

        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        net = Network.FILES["sys_net"]
        mode = "tx" if mode == "up" else "rx"
        stat_file = Path(net, dev, "statistics", f"{mode}_bytes")
        return int(open_read(stat_file))


class Misc(AbstractMisc):
    """ A Linux implementation of the AbstractMisc class """

    FILES = {
        "proc": Path("/proc"),
        "sys_backlight": Path("/sys/devices/backlight"),
    }

    def _vol(self):
        systems = {"pulseaudio": Misc._vol_pulseaudio}
        reg = re.compile(r"|".join(systems.keys()))

        vol = None
        proc = Misc.FILES["proc"]
        pids = (open_read(d.joinpath("cmdline")) for d in proc.iterdir()
                if d.is_dir() and d.name.isdigit())
        audio = (reg.search(i) for i in pids if i and reg.search(i))
        audio = next(audio, None)

        if audio is not None:
            try:
                vol = systems[audio.group(0)]()
            except KeyError:
                vol = None

        return vol

    def _scr(self):
        scr = None
        backlight_path = Misc.FILES["sys_backlight"]

        if backlight_path.exists():
            scr_files = (f for f in backlight_path.rglob("*")
                         if "kbd" not in f.name and "backlight" not in f.name)
            scr_dir = next(scr_files, None)

            if scr_dir is not None:
                curr = int(open_read(scr_dir.joinpath("brightness")))
                max_scr = int(open_read(scr_dir.joinpath("max_brightness")))
                scr = percent(curr, max_scr)

        return scr

    @staticmethod
    @lru_cache(maxsize=1)
    def _vol_pulseaudio():
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


class Linux(System):
    """ A Linux implementation of the abstract System class """

    def __init__(self, options):
        super(Linux, self).__init__(options,
                                    cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                    bat=Battery.detect_battery(), net=Network,
                                    wm=self.detect_window_manager(),
                                    misc=Misc)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "Xorg": wm.Xorg,
        }
