#!/usr/bin/env python3
# pylint: disable=abstract-method
# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=no-self-use

""" Linux specific module """

import re
import shutil

from argparse import Namespace
from functools import lru_cache
from pathlib import Path as p

from .abstract import (System, AbstractCpu, AbstractMemory, AbstractSwap,
                       AbstractDisk, AbstractBattery, AbstractNetwork,
                       AbstractMisc)
from ..tools.storage import Storage
from ..tools.utils import open_read, run, percent, _round


class Cpu(AbstractCpu):
    """ A Linux implementation of the AbstractCpu class """

    @property
    @lru_cache(maxsize=1)
    def cpu_file(self):
        """ Returns cached /proc/cpuinfo """
        return open_read("/proc/cpuinfo")

    @property
    @lru_cache(maxsize=1)
    def cores(self):
        return len(re.findall(r"^processor", self.cpu_file, re.M))

    def _cpu_speed(self):
        speed_reg = re.compile(r"(bios_limit|(scaling|cpuinfo)_max_freq)$")
        cpu = re.search(r"model name\s+: (.*)", self.cpu_file, re.M).group(1)

        check = lambda f: speed_reg.search(str(f))
        speed_dir = "/sys/devices/system/cpu"
        speed = next((f for f in p(speed_dir).rglob("*") if check(f)), None)

        if speed is not None:
            speed = float(open_read(speed))
            speed = _round(speed / 1e6, 2)

        return cpu, speed

    @property
    def load_avg(self):
        load = open_read("/proc/loadavg").split(" ")
        return load[0] if self.options.cpu_load_short else " ".join(load[:3])

    @property
    def fan(self):
        fan = None
        fan_dir = "/sys/devices/platform"
        glob = "fan1_input"
        files = (f for f in p(fan_dir).rglob(glob))

        fan = next(files, None)
        if fan is not None:
            fan = int(open_read(fan).strip())

        return fan

    @property
    def temp(self):
        check = lambda f: p.exists(p(f)) and "temp" in open_read(f)
        glob = lambda d: p(d).glob("*")

        temp = None
        files = (f for f in glob("/sys/class/hwmon") if check("{}/name".format(f)))

        temp_dir = next(files, None)
        if temp_dir is not None:
            files = sorted([f for f in p(temp_dir).glob("temp*_input")])
            if files:
                temp = float(open_read(str(files[0]))) / 1000

        return temp

    def _uptime(self):
        return int(float(open_read("/proc/uptime").strip().split(" ")[0]))


@lru_cache(maxsize=1)
def mem_file():
    """ Returns cached /proc/meminfo """
    reg = re.compile(r"\s+|kB")
    _mem_file = open_read("/proc/meminfo").strip().split("\n")
    return dict(reg.sub("", i).split(":", 1) for i in _mem_file)


class Memory(AbstractMemory):
    """ A Linux implementation of the AbstractMemory class """

    @property
    def used(self):
        keys = [["MemTotal", "Shmem"],
                ["MemFree", "Buffers", "Cached", "SReclaimable"]]
        used = sum([int(mem_file()[i]) for i in keys[0]])
        used -= sum([int(mem_file()[i]) for i in keys[1]])
        used = Storage(value=used, prefix="KiB",
                       rounding=self.options.mem_used_round)
        used.prefix = self.options.mem_used_prefix
        return used

    @property
    def total(self):
        total = Storage(value=int(mem_file()["MemTotal"]), prefix="KiB",
                        rounding=self.options.mem_total_round)
        total.prefix = self.options.mem_total_prefix
        return total


class Swap(AbstractSwap):
    """ A Linux implementation of the AbstractSwap class """

    @property
    def used(self):
        used = int(mem_file()["SwapTotal"]) - int(mem_file()["SwapFree"])
        used = Storage(value=used, prefix="KiB",
                       rounding=self.options.swap_used_round)
        used.prefix = self.options.swap_used_prefix
        return used

    @property
    def total(self):
        total = Storage(value=int(mem_file()["SwapTotal"]), prefix="KiB",
                        rounding=self.options.swap_total_round)
        total.prefix = self.options.swap_total_prefix
        return total


class Disk(AbstractDisk):
    """ A Linux implementation of the AbstractDisk class """

    @property
    def _DF_FLAGS(self):
        return ["df", "-P"]

    @property
    @lru_cache(maxsize=1)
    def _lsblk(self):
        columns = ["KNAME", "NAME", "LABEL", "PARTLABEL",
                   "FSTYPE", "MOUNTPOINT"]

        lsblk = dict()

        if self.dev is not None:
            cmd = ["lsblk", "--output", ",".join(columns),
                   "--paths", "--pairs"] + list(self.original_dev.values())

            for line in run(cmd).strip().split("\n"):
                out = re.findall(r"[^\"\s]\S*|\".+?", line)
                out = dict(re.sub("\"", "", i).split("=", 1) for i in out)
                lsblk[out["KNAME"]] = out

        return lsblk

    @property
    def name(self):
        labels = ["LABEL", "PARTLABEL"]
        return {k: next((v[i] for i in labels if v[i]), None)
                for k, v in self._lsblk.items()}

    @property
    def partition(self):
        return {k: v["FSTYPE"] for k, v in self._lsblk.items()}


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
    check = lambda d: p(d).exists()

    avail = {
        "{}/charge_now".format(bat_dir()): BatteryAmp,
        "{}/energy_now".format(bat_dir()): BatteryWatt
    }

    return next((v for k, v in avail.items() if check(k)), BatteryStub)


@lru_cache(maxsize=1)
def bat_dir():
    """ Returns the path for the battery directory """
    check = lambda f: p(f).exists() and bool(int(open_read(f)))
    _bat_dir = p("/sys/class/power_supply").glob("*BAT*")
    _bat_dir = (d for d in _bat_dir if check("{}/present".format(d)))
    return next(_bat_dir, None)


class Battery(AbstractBattery):
    """ A Linux implementation of the AbstractBattery class """

    @property
    @lru_cache(maxsize=1)
    def status(self):
        """ Returns cached battery status file """
        return open_read("{}/status".format(bat_dir())).strip()

    @property
    @lru_cache(maxsize=1)
    def current_charge(self):
        """ Returns cached battery current charge file """
        return None if bat_dir() is None else int(open_read(self.current))

    @property
    @lru_cache(maxsize=1)
    def full_charge(self):
        """ Returns cached battery full charge file """
        return None if bat_dir() is None else int(open_read(self.full))

    @property
    @lru_cache(maxsize=1)
    def drain_rate(self):
        """ Returns cached battery drain rate file """
        return None if bat_dir() is None else int(open_read(self.drain))

    @lru_cache(maxsize=1)
    def _compare_status(self, query):
        """ Compares status to query """
        return None if bat_dir() is None else self.status == query

    @property
    def is_present(self):
        return bat_dir() is not None

    @property
    def is_charging(self):
        return self._compare_status("Charging")

    @property
    def is_full(self):
        return self._compare_status("Full")

    @property
    def percent(self):
        perc = None
        if bat_dir() is not None:
            current_charge = self.current_charge
            full_charge = self.full_charge

            perc = percent(current_charge, full_charge)
            perc = _round(perc, self.options.bat_percent_round)

        return perc

    @property
    def _time(self):
        remaining = 0
        if bat_dir() is not None and self.drain_rate:
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
        return "{}/charge_now".format(bat_dir())

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full charge filename """
        return "{}/charge_full".format(bat_dir())

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns current filename """
        return "{}/current_now".format(bat_dir())

    @property
    def power(self):
        power = None
        if bat_dir() is not None:
            voltage = int(open_read("{}/voltage_now".format(bat_dir())))
            power = (self.drain_rate * voltage) / 1e12
            power = _round(power, self.options.bat_power_round)

        return power


class BatteryWatt(Battery):
    """ Sub-Battery class for systems that stores battery info in watt """

    @property
    @lru_cache(maxsize=1)
    def current(self):
        """ Returns current energy filename """
        return "{}/energy_now".format(bat_dir())

    @property
    @lru_cache(maxsize=1)
    def full(self):
        """ Returns full energy filename """
        return "{}/energy_full".format(bat_dir())

    @property
    @lru_cache(maxsize=1)
    def drain(self):
        """ Returns power filename """
        return "{}/power_now".format(bat_dir())

    @property
    def power(self):
        return _round(self.drain_rate / 1e6, self.options.bat_power_round)


class BatteryStub(AbstractBattery):
    """ Sub-Battery class for systems that has no battery """

    @property
    def is_present(self):
        return False

    @property
    def is_charging(self):
        return None

    @property
    def is_full(self):
        return None

    @property
    def percent(self):
        return None

    @property
    def _time(self):
        return 0

    @property
    def power(self):
        return None


class Network(AbstractNetwork):
    """ A Linux implementation of the AbstractNetwork class """

    @property
    def _LOCAL_IP_CMD(self):
        return ["ip", "address", "show", "dev"]

    @property
    def dev(self):
        check = lambda f: open_read("{}/operstate".format(f)).strip() == "up"
        find = lambda d: p(d).glob("[!v]*")
        return next((f.name for f in find("/sys/class/net") if check(f)), None)

    @property
    def _ssid(self):
        ssid_cmd = None
        ssid_reg = None
        dev = self.dev

        if dev is not None:
            try:
                wifi_path = "/proc/net/wireless"
                wifi_out = open_read(wifi_path).strip().split("\n")
                if len(wifi_out) >= 3 and shutil.which("iw"):
                    ssid_cmd = ("iw", "dev", dev, "link")
                    ssid_reg = re.compile(r"^SSID: (.*)$")
            except FileNotFoundError:
                ssid_cmd = None
                ssid_reg = None

        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        net = "/sys/class/net/{}/statistics/{{}}_bytes".format(dev)
        stat_file = net.format("tx" if mode == "up" else "rx")
        return int(open_read(stat_file))


class Misc(AbstractMisc):
    """ A Linux implementation of the AbstractMisc class """

    @property
    def vol(self):
        check = lambda d: d.is_dir() and d.name.isdigit()
        extract = lambda f: open_read("{}/cmdline".format(f))

        systems = {"pulseaudio": get_vol_pulseaudio}

        reg = re.compile(r"|".join(systems.keys()))

        vol = None
        pids = (extract(i) for i in p("/proc").iterdir() if check(i))
        audio = next((reg.search(i) for i in pids if i and reg.search(i)), None)

        if audio is not None:
            try:
                vol = systems[audio.group(0)]()
                if vol is not None:
                    vol = _round(vol, self.options.misc_volume_round)
            except KeyError:
                vol = None

        return vol

    @property
    def scr(self):
        scr = None
        backlight_path = p("/sys/devices/backlight")

        if backlight_path.exists():
            check = lambda f: "kbd" not in f and "backlight" in f
            scr_files = (f for f in backlight_path.rglob("*") if check(f.name))
            scr_dir = next(scr_files, None)

            if scr_dir is not None:
                curr = int(open_read("{}/brightness".format(scr_dir)))
                max_scr = int(open_read("{}/max_brightness".format(scr_dir)))
                scr = percent(curr, max_scr)
                scr = _round(scr, self.options.misc_screen_round)

        return scr


def get_vol_pulseaudio():
    """ Return system volume using pulse audio """
    default_reg = re.compile(r"^set-default-sink (.*)$", re.M)
    pac_dump = run(["pacmd", "dump"])

    vol = None
    default = default_reg.search(pac_dump)
    if default is not None:
        vol_reg = r"^set-sink-volume {} 0x(.*)$".format(default.group(1))
        vol_reg = re.compile(vol_reg, re.M)
        vol = vol_reg.search(pac_dump)
        if vol is not None:
            vol = percent(int(vol.group(1), 16), 0x10000)

    return vol


class Linux(System):
    """ A Linux implementation of the abstract System class """

    def __init__(self, options):
        super(Linux, self).__init__(options, aux=None, cpu=Cpu, mem=Memory,
                                    swap=Swap, disk=Disk, bat=detect_battery(),
                                    net=Network, misc=Misc)
