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

    _FILES = {
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
        return open_read(Cpu._FILES["proc_cpu"])

    @property
    @lru_cache(maxsize=1)
    def _cpu_speed_file_path(self):
        speed_reg = re.compile(r"(bios_limit|(scaling|cpuinfo)_max_freq)$")
        speed_dir = Cpu._FILES["sys_cpu"]
        speed_glob = speed_dir.rglob("*")
        path = next(filter(speed_reg.search, map(str, speed_glob)), None)
        return path

    @property
    @lru_cache(maxsize=1)
    def _cpu_temp_file_paths(self):
        def check(_file):
            _file = _file.joinpath("name")
            _file_contents = open_read(_file)
            if _file_contents is None:
                return False
            return "temp" in open_read(_file)

        temp_dir_base = Cpu._FILES["sys_hwmon"]
        temp_dir_glob = temp_dir_base.glob("*")
        temp_dir = next(filter(check, temp_dir_glob), None)

        if temp_dir is None:
            return None

        temp_paths = sorted(temp_dir.glob("temp*_input"))
        return temp_paths

    @property
    @lru_cache(maxsize=1)
    def _cpu_fan_file_path(self):
        fan_dir_base = Cpu._FILES["sys_platform"]
        fan_dir_glob = fan_dir_base.rglob("fan1_input")
        fan_path = next(fan_dir_glob, None)
        return fan_path

    def cores(self, options=None):
        return len(re.findall(r"^processor", self._cpu_file, re.M))

    def _cpu_string(self):
        match = re.search(r"model name\s+: (.*)", self._cpu_file, re.M)
        if match is None:
            return None

        cpu = match.group(1)
        return cpu

    def _cpu_speed(self):
        speed_path = self._cpu_speed_file_path
        if speed_path is None:
            return None

        speed = open_read(speed_path)
        if speed is None or not speed.strip().isnumeric():
            return None

        speed = round_trim(float(speed) / 1e6, 2)
        return speed

    def _load_avg(self):
        load_path = Cpu._FILES["proc_load"]
        load_file = open_read(load_path)
        if load_file is None:
            return None

        load = load_file.strip().split()[:3]
        return load

    def fan(self, options=None):
        fan_path = self._cpu_fan_file_path
        if fan_path is None:
            return None

        fan = open_read(fan_path)
        if fan is None or not fan.strip().isnumeric():
            return None

        fan = int(fan.strip())
        return fan

    def _temp(self):
        temp_paths = self._cpu_temp_file_paths
        if not temp_paths:
            return None

        temp_path = next(iter(temp_paths))
        temp = open_read(temp_path)
        if temp is None:
            return None

        temp = float(temp) / 1000
        return temp

    def _uptime(self):
        uptime = None
        uptime_path = Cpu._FILES["proc_uptime"]
        uptime_file = open_read(uptime_path)
        if uptime_file is None:
            return None

        uptime = int(float(uptime_file.strip().split(" ")[0]))
        return uptime


@lru_cache(maxsize=1)
def _mem_file():
    """ Returns cached /proc/meminfo """
    reg = re.compile(r"\s+|kB")
    mem_file = open_read("/proc/meminfo")
    if mem_file is None:
        return dict()

    mem_file = mem_file.strip().splitlines()
    mem_file = dict(reg.sub("", i).split(":", 1) for i in mem_file)
    mem_file = {k: int(v) for k, v in mem_file.items()}
    return mem_file


class Memory(AbstractMemory):
    """ A Linux implementation of the AbstractMemory class """

    def _used(self):
        mem_file = _mem_file()
        keys = [["MemTotal", "Shmem"],
                ["MemFree", "Buffers", "Cached", "SReclaimable"]]
        used = sum(mem_file.get(i, 0) for i in keys[0])
        used -= sum(mem_file.get(i, 0) for i in keys[1])
        return used, "KiB"

    def _total(self):
        return _mem_file().get("MemTotal", 0), "KiB"


class Swap(AbstractSwap):
    """ A self implementation of the AbstractSwap class """

    def _used(self):
        mem_file = _mem_file()
        used = mem_file.get("SwapTotal", 0) - mem_file.get("SwapFree", 0)
        return used, "KiB"

    def _total(self):
        return _mem_file().get("SwapTotal", 0), "KiB"


class Disk(AbstractDisk):
    """ A Linux implementation of the AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P"]

    @property
    @lru_cache(maxsize=1)
    def _lsblk_exe(self):
        """ Returns the path to the lsblk executable """
        return shutil.which("lsblk")

    @property
    @lru_cache(maxsize=1)
    def _lsblk_entries(self):
        """
        Returns the output of lsblk in a dictionary with devices as keys
        """
        if not self._lsblk_exe:
            return None

        columns = ["NAME", "LABEL", "PARTLABEL", "FSTYPE"]
        cmd = [self._lsblk_exe, "--output", ",".join(columns), "--paths",
               "--pairs"]
        lsblk_out = run(cmd)
        if lsblk_out is None:
            return None

        lsblk_out = lsblk_out.strip().splitlines()
        lsblk_entries = dict()
        for line in lsblk_out:
            out = shlex.split(line)
            out = dict(re.sub("\"", "", i).split("=", 1) for i in out)
            lsblk_entries[out["NAME"]] = out

        return lsblk_entries

    def name(self, options=None):
        devs = self._original_dev(options)
        if devs is None:
            return None

        lsblk_entries = self._lsblk_entries
        if lsblk_entries is None:
            return {k: None for k in devs.keys()}

        labels = ["LABEL", "PARTLABEL"]
        names = {k: next((v[i] for i in labels if v[i]), None)
                 for k, v in lsblk_entries.items() if k in devs}
        return names

    def partition(self, options=None):
        devs = self._original_dev(options)
        if devs is None:
            return None

        lsblk_entries = self._lsblk_entries
        if lsblk_entries is None:
            return {k: None for k in devs.keys()}

        partitions = {k: v["FSTYPE"]
                      for k, v in lsblk_entries.items() if k in devs}
        return partitions


class Battery(AbstractBattery):
    """ A Linux implementation of the AbstractBattery class """

    _FILES = {
        "sys_power_supply": Path("/sys/class/power_supply"),
    }

    @property
    @abstractmethod
    def _current(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def _full(self):
        """ Abstract current class to be implemented """

    @property
    @abstractmethod
    def _drain(self):
        """ Abstract current class to be implemented """

    @property
    @lru_cache(maxsize=1)
    def _status(self):
        """ Returns cached battery status file """
        bat_dir = Battery.directory()
        if bat_dir is None:
            return None

        status_path = bat_dir.joinpath("status")
        status = open_read(status_path)
        if status is None:
            return None

        status = status.strip()
        return status

    @property
    @lru_cache(maxsize=1)
    def _current_charge(self):
        """ Returns cached battery current charge file """
        bat_dir = Battery.directory()
        current_filename = self._current

        if bat_dir is None:
            return None

        if current_filename is None:
            return None

        current_path = bat_dir.joinpath(current_filename)
        current_charge = open_read(current_path)
        if current_charge is None:
            return None

        current_charge = current_charge.strip()
        if not current_charge.isnumeric():
            return None

        current_charge = int(current_charge)
        return current_charge

    @property
    @lru_cache(maxsize=1)
    def _full_charge(self):
        """ Returns cached battery full charge file """
        bat_dir = Battery.directory()
        full_filename = self._full

        if bat_dir is None:
            return None

        if full_filename is None:
            return None

        full_path = bat_dir.joinpath(full_filename)
        full_charge = open_read(full_path)
        if full_charge is None:
            return None

        full_charge = full_charge.strip()
        if not full_charge.isnumeric():
            return None

        full_charge = int(full_charge)
        return full_charge

    @property
    @lru_cache(maxsize=1)
    def _drain_rate(self):
        """ Returns cached battery drain rate file """
        bat_dir = Battery.directory()
        drain_filename = self._drain

        if bat_dir is None:
            return None

        if drain_filename is None:
            return None

        drain_path = bat_dir.joinpath(drain_filename)
        drain_rate = open_read(drain_path)
        if drain_rate is None:
            return None

        drain_rate = drain_rate.strip()
        if not drain_rate.isnumeric():
            return None

        drain_rate = int(drain_rate)
        return drain_rate

    @lru_cache(maxsize=1)
    def _compare_status(self, query):
        """ Compares status to query """
        bat_dir = Battery.directory()
        if bat_dir is not None:
            return self._status == query
        return None

    def is_present(self, options=None):
        return Battery.directory() is not None

    def is_charging(self, options=None):
        return self._compare_status("Charging")

    def is_full(self, options=None):
        return self._compare_status("Full")

    def _percent(self):
        return self._current_charge, self._full_charge

    def _time(self):
        if not self.is_present or not self._drain_rate:
            return 0

        charge = self._current_charge
        if self.is_charging():
            charge = self._full_charge - charge

        remaining = int((charge / self._drain_rate) * 3600)
        return remaining

    def _power(self):
        pass

    @staticmethod
    @lru_cache(maxsize=1)
    def directory():
        """ Returns the path for the battery directory """
        def check(_file):
            _file = _file.joinpath("present")
            if not _file.exists():
                return False

            _file_contents = open_read(_file)
            if (
                    _file_contents is None
                    or not _file_contents.strip().isnumeric()
            ):
                return False

            return bool(int(_file_contents))

        _dir = Battery._FILES["sys_power_supply"]
        _dir_glob = _dir.glob("*BAT*")
        bat_dir = next(filter(check, _dir_glob), None)
        return bat_dir

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
    def _current(self):
        """ Returns current charge filename """
        return "charge_now"

    @property
    @lru_cache(maxsize=1)
    def _full(self):
        """ Returns full charge filename """
        return "charge_full"

    @property
    @lru_cache(maxsize=1)
    def _drain(self):
        """ Returns current filename """
        return "current_now"

    def _power(self):
        bat_dir = Battery.directory()
        if bat_dir is None:
            return None

        voltage_path = bat_dir.joinpath("voltage_now")
        voltage = open_read(voltage_path)
        drain_rate = self._drain_rate

        if voltage is None:
            return None

        voltage = voltage.strip()
        if not voltage.isnumeric():
            return None

        if drain_rate is None:
            return None

        voltage = int(voltage)
        power = (drain_rate * voltage) / 1_000_000_000_000
        return power


class BatteryWatt(Battery):
    """ Sub-Battery class for systems that stores battery info in watt """

    @property
    @lru_cache(maxsize=1)
    def _current(self):
        """ Returns current energy filename """
        return "energy_now"

    @property
    @lru_cache(maxsize=1)
    def _full(self):
        """ Returns full energy filename """
        return "energy_full"

    @property
    @lru_cache(maxsize=1)
    def _drain(self):
        """ Returns power filename """
        return "power_now"

    def _power(self):
        drain_rate = self._drain_rate
        if drain_rate is None:
            return None
        return drain_rate / 1_000_000


class Network(AbstractNetwork):
    """ A Linux implementation of the AbstractNetwork class """

    _FILES = {
        "sys_net": Path("/sys/class/net"),
        "proc_wifi": Path("/proc/net/wireless"),
    }

    @property
    def _LOCAL_IP_CMD(self):
        return ["ip", "address", "show", "dev"]

    @property
    @lru_cache(maxsize=1)
    def _iw_exe(self):
        """ Returns the path to the iw executable """
        return shutil.which("iw")

    def dev(self, options=None):
        def check(_file):
            _file = _file.joinpath("operstate")
            _file_contents = open_read(_file)
            if _file_contents is None:
                return False
            return "up" in _file_contents

        # Skip virtual network devices
        files = Network._FILES["sys_net"].glob("[!v]*")
        dev_dir = next(filter(check, files), None)
        if dev_dir is None:
            return None
        return dev_dir.name

    def _ssid(self):
        dev = self.dev()
        if dev is None:
            return None, None

        wifi_path = Network._FILES["proc_wifi"]
        wifi_out = open_read(wifi_path)
        if wifi_out is None:
            return None, None

        wifi_out = wifi_out.strip().splitlines()
        if len(wifi_out) < 3 or not self._iw_exe:
            return None, None

        ssid_cmd = (self._iw_exe, "dev", dev, "link")
        ssid_reg = re.compile(r"^SSID: (.*)$")
        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        net = Network._FILES["sys_net"]
        if mode == "up":
            mode = "tx"
        else:
            mode = "rx"

        stat_file = Path(net, dev, "statistics", f"{mode}_bytes")
        stat = open_read(stat_file)
        if stat is None:
            return None

        stat = int(stat)
        return stat


class Misc(AbstractMisc):
    """ A Linux implementation of the AbstractMisc class """

    _FILES = {
        "proc": Path("/proc"),
        "sys_backlight": Path("/sys/devices/backlight"),
    }

    def _vol(self):
        systems = {"pulseaudio": Misc._vol_pulseaudio}
        reg = re.compile(r"|".join(systems.keys()))

        proc = Misc._FILES["proc"]
        pids = (open_read(d.joinpath("cmdline")) for d in proc.iterdir()
                if d.is_dir() and d.name.isdigit())
        audio = (reg.search(i) for i in pids if i and reg.search(i))
        audio = next(audio, None)

        if audio is None:
            return None

        try:
            vol = systems[audio.group(0)]()
        except KeyError:
            vol = None

        return vol

    def _scr(self):
        def check(_file):
            _filename = _file.name
            return "kbd" not in _filename and "backlight" not in _filename

        backlight_path = Misc._FILES["sys_backlight"]
        if not backlight_path.exists():
            return None, None

        backlight_glob = backlight_path.rglob("*")
        scr_dir = next(filter(check, backlight_glob), None)
        if scr_dir is None:
            return None, None

        current_scr = open_read(scr_dir.joinpath("brightness"))
        max_scr = open_read(scr_dir.joinpath("max_brightness"))

        if current_scr is None or max_scr is None:
            return None, None

        current_scr = current_scr.strip()
        max_scr = max_scr.strip()

        if not current_scr.isnumeric() or not max_scr.isnumeric():
            return None, None

        return current_scr, max_scr

    @staticmethod
    @lru_cache(maxsize=1)
    def _vol_pulseaudio():
        """ Return system volume using pulse audio """
        default_reg = re.compile(r"^set-default-sink (.*)$", re.M)
        pacmd_exe = shutil.which("pacmd")
        if not pacmd_exe:
            return None

        pac_dump = run([pacmd_exe, "dump"])
        if pac_dump is None:
            return None

        default = default_reg.search(pac_dump)
        if default is None:
            return None

        vol_reg = fr"^set-sink-volume {default.group(1)} 0x(.*)$"
        vol_reg = re.compile(vol_reg, re.M)
        vol = vol_reg.search(pac_dump)

        if vol is None:
            return None

        vol = vol.group(1)
        vol = int(vol, 16)
        vol = percent(vol, 0x10000)
        return vol


class Linux(System):
    """ A Linux implementation of the abstract System class """

    def __init__(self, default_options):
        super(Linux, self).__init__(default_options,
                                    cpu=Cpu, mem=Memory, swap=Swap, disk=Disk,
                                    bat=Battery.detect_battery(), net=Network,
                                    wm=self.detect_window_manager(),
                                    misc=Misc)

    @property
    def _SUPPORTED_WMS(self):
        return {
            "Xorg": wm.Xorg,
        }
