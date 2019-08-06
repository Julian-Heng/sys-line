#!/usr/bin/env python3
# pylint: disable=no-self-use,no-member

""" Linux specific module """

import re
import shutil

from pathlib import Path as p

from .abstract import (System,
                       AbstractCpu,
                       AbstractMemory,
                       AbstractSwap,
                       AbstractDisk,
                       AbstractBattery,
                       AbstractNetwork,
                       AbstractMisc)
from ..tools.storage import Storage
from ..tools.utils import open_read, run, percent, _round


class Linux(System):
    """
    A Linux implementation of the abstract
    System class in abstract.py
    """

    def __init__(self, os_name, options):
        domains = {
            "cpu": Cpu,
            "mem": Memory,
            "swap": Swap,
            "disk": Disk,
            "bat": detect_battery(),
            "net": Network,
            "misc": Misc
        }

        super(Linux, self).__init__(domains, os_name, options)


class Cpu(AbstractCpu):
    """ Linux implementation of AbstractCpu class """

    def __init__(self, options):
        super(Cpu, self).__init__(options)
        self.cpu_file = None


    def get_cores(self):
        if self.cpu_file is None:
            self.cpu_file = open_read("/proc/cpuinfo")
        return len(re.findall(r"^processor", self.cpu_file, re.M))


    def _get_cpu_speed(self):
        if self.cpu_file is None:
            self.cpu_file = open_read("/proc/cpuinfo")

        speed_reg = re.compile(r"(bios_limit|(scaling|cpuinfo)_max_freq)$")
        cpu = re.search(r"model name\s+: (.*)", self.cpu_file, re.M).group(1)

        check = lambda f, r=speed_reg: r.search(str(f))
        speed_dir = "/sys/devices/system/cpu"
        speed_files = (f for f in p(speed_dir).rglob("*") if check(f))

        speed = next(speed_files, None)
        if speed is not None:
            speed = float(open_read(speed))
            speed = "{:.2f}".format(speed / 1000000)

        return cpu, speed


    def get_load_avg(self):
        load_file = "/proc/loadavg"
        load = open_read(load_file).split(" ")
        return load[0] if self.options.cpu_load_short else " ".join(load[:3])


    def get_fan(self):
        fan = None
        fan_dir = "/sys/devices/platform"
        glob = "fan1_input"
        files = (f for f in p(fan_dir).rglob(glob))

        fan = next(files, None)
        if fan is not None:
            fan = int(open_read(fan).strip())

        return fan


    def get_temp(self):
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


    def _get_uptime_sec(self):
        return int(float(open_read("/proc/uptime").strip().split(" ")[0]))


class Memory(AbstractMemory):
    """ Linux implementation of AbstractMemory class """

    def __init__(self, options):
        super(Memory, self).__init__(options)
        reg = re.compile(r"\s+|kB")
        mem_file = open_read("/proc/meminfo").strip().split("\n")
        mem_file = [reg.sub("", i) for i in mem_file]
        self.mem_file = dict(i.split(":", 1) for i in mem_file)


    def get_used(self):
        keys = [["MemTotal", "Shmem"],
                ["MemFree", "Buffers", "Cached", "SReclaimable"]]
        used = sum([int(self.mem_file[i]) for i in keys[0]])
        used -= sum([int(self.mem_file[i]) for i in keys[1]])
        used = Storage(value=used, prefix="KiB",
                       rounding=self.options.mem_used_round)
        used.set_prefix(self.options.mem_used_prefix)
        return used


    def get_total(self):
        total = Storage(int(self.mem_file["MemTotal"]), prefix="KiB",
                        rounding=self.options.mem_total_round)

        total.set_prefix(self.options.mem_total_prefix)
        return total


class Swap(AbstractSwap):
    """ Linux implementation of AbstractSwap class """

    def __init__(self, options):
        super(Swap, self).__init__(options)
        reg = re.compile(r"\s+|kB")
        mem_file = open_read("/proc/meminfo").strip().split("\n")
        mem_file = [reg.sub("", i) for i in mem_file]
        self.mem_file = dict(i.split(":", 1) for i in mem_file)


    def get_used(self):
        used = int(self.mem_file["SwapTotal"])
        used -= int(self.mem_file["SwapFree"])
        used = Storage(value=used, prefix="KiB",
                       rounding=self.options.swap_used_round)
        used.set_prefix(self.options.swap_used_prefix)
        return used


    def get_total(self):
        total = Storage(int(self.mem_file["SwapTotal"]), prefix="KiB",
                        rounding=self.options.swap_total_round)

        total.set_prefix(self.options.swap_total_prefix)
        return total


class Disk(AbstractDisk):
    """ Linux implementation of AbstractDisk class """

    def __init__(self, options):
        super(Disk, self).__init__(options)
        self.df_flags = ["df", "-P"]
        self.lsblk = None


    def __set_lsblk(self):
        if self.get("dev") is None:
            self.call("dev")

        columns = ["KNAME", "NAME", "LABEL", "PARTLABEL",
                   "FSTYPE", "MOUNTPOINT"]
        cmd = ["lsblk", "--output", ",".join(columns),
               "--paths", "--pairs", self.get("dev")]

        lsblk = re.findall(r"[^\"\s]\S*|\".+?", run(cmd))
        self.lsblk = dict(re.sub("\"", "", i).split("=", 1) for i in lsblk)


    def __lookup_lsblk(self, key):
        if self.lsblk is None:
            self.__set_lsblk()
        return self.lsblk[key]


    def get_name(self):
        name = self.__lookup_lsblk("LABEL")
        if not name:
            name = self.__lookup_lsblk("PARTLABEL")

        return name


    def get_mount(self):
        return self.__lookup_lsblk("MOUNTPOINT")


    def get_partition(self):
        return self.__lookup_lsblk("FSTYPE")


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
    bat_dir = _get_battery_dir()
    check = lambda d: p(d).exists()

    avail = {
        "{}/charge_now".format(bat_dir): BatteryAmp,
        "{}/energy_now".format(bat_dir): BatteryWatt
    }

    return next((v for k, v in avail.items() if check(k)), BatteryStub)


def _get_battery_dir():
    check = lambda f: p(f).exists() and bool(int(open_read(f)))
    bat_dir = p("/sys/class/power_supply").glob("*BAT*")
    bat_dir = (d for d in bat_dir if check("{}/present".format(d)))
    return next(bat_dir, None)


class Battery(AbstractBattery):
    """ Linux implementation of AbstractBattery class """

    def __init__(self, options):
        super(Battery, self).__init__(options)
        self.bat_dir = _get_battery_dir()
        self.status = None
        self.current_charge = None
        self.full_charge = None
        self.drain_rate = None


    def __get_status(self):
        self.status = open_read("{}/status".format(self.bat_dir)).strip()


    def _get_current_charge(self):
        if self.bat_dir is not None:
            self.current_charge = int(open_read(self.files["current"]))


    def _get_full_charge(self):
        if self.bat_dir is not None:
            self.full_charge = int(open_read(self.files["full"]))


    def _get_drain_rate(self):
        if self.bat_dir is not None:
            self.drain_rate = int(open_read(self.files["drain"]))


    def __compare_status(self, query):
        if self.status is None:
            self.__get_status()
        return None if self.bat_dir is None else self.status == query


    def get_is_present(self):
        return self.bat_dir is not None


    def get_is_charging(self):
        return self.__compare_status("Charging")


    def get_is_full(self):
        return self.__compare_status("Full")


    def get_percent(self):
        perc = None
        if self.bat_dir is not None:
            if self.current_charge is None:
                self._get_current_charge()
            if self.full_charge is None:
                self._get_full_charge()

            perc = percent(self.current_charge, self.full_charge)
            perc = _round(perc, self.options.bat_percent_round)

        return perc


    def _get_time(self):
        time = None
        if self.bat_dir is not None:
            if self.get("is_charging") is None:
                self.call("is_charging")
            if self.current_charge is None:
                self._get_current_charge()
            if self.full_charge is None:
                self._get_full_charge()
            if self.drain_rate is None:
                self._get_drain_rate()
                if self.drain_rate == 0:
                    return 0

            charge = self.current_charge

            if self.get("is_charging"):
                charge = self.full_charge - charge

            time = int((charge / self.drain_rate) * 3600)

        return time


    def get_power(self):
        """ To be implemented by BatteryAmp or BatteryWatt """


class BatteryAmp(Battery):
    """ Stores filenames for batteries using amps """

    def __init__(self, options):
        super(BatteryAmp, self).__init__(options)
        self.files = {
            "current": "{}/charge_now".format(self.bat_dir),
            "full": "{}/charge_full".format(self.bat_dir),
            "drain": "{}/current_now".format(self.bat_dir)
        }


    def get_power(self):
        power = None
        if self.bat_dir is not None:
            if self.drain_rate is None:
                self._get_drain_rate()

            voltage = int(open_read("{}/voltage_now".format(self.bat_dir)))
            power = (self.drain_rate * voltage) / 10e11
            power = _round(power, self.options.bat_power_round)

        return power


class BatteryWatt(Battery):
    """ Stores filenames for batteries using watts """

    def __init__(self, options):
        super(BatteryWatt, self).__init__(options)
        self.files = {
            "current": "{}/energy_now".format(self.bat_dir),
            "full": "{}/energy_full".format(self.bat_dir),
            "drain": "{}/power_now".format(self.bat_dir)
        }


    def get_power(self):
        if self.drain_rate is None:
            self._get_drain_rate()

        return _round(self.drain_rate / 10e5, self.options.bat_power_round)


class BatteryStub(AbstractBattery):
    """ Battery stub class for desktop machines """

    def get_is_present(self):
        return False


    def get_is_charging(self):
        raise NotImplementedError


    def get_is_full(self):
        raise NotImplementedError


    def get_percent(self):
        raise NotImplementedError


    def _get_time(self):
        return 0


    def get_power(self):
        raise NotImplementedError


class Network(AbstractNetwork):
    """ Linux implementation of AbstractNetwork class """

    def __init__(self, options):
        super(Network, self).__init__(options)
        self.local_ip_cmd = ["ip", "address", "show", "dev"]


    def get_dev(self):
        check = lambda f: open_read("{}/operstate".format(f)).strip() == "up"
        find = lambda d: p(d).glob("[!v]*")
        return next((f.name for f in find("/sys/class/net") if check(f)), None)


    def _get_ssid(self):
        ssid_exe = None
        regex = None

        dev = self.get("dev")
        if dev is None:
            self.call("dev")
            dev = self.get("dev")

        if dev is not None:
            wifi = "/proc/net/wireless"
            if (len(open_read(wifi).strip().split("\n"))) >= 3:
                if shutil.which("iw"):
                    ssid_exe = ["iw", "dev", dev, "link"]
                    regex = re.compile("^SSID: (.*)$")

        return ssid_exe, regex


    def _get_bytes_delta(self, dev, mode):
        net = "/sys/class/net/{}/statistics/{{}}_bytes".format(dev)
        stat_file = net.format("tx" if mode == "up" else "rx")
        return int(open_read(stat_file))


class Misc(AbstractMisc):
    """ Linux implementation of AbstractMisc class """

    def get_vol(self):
        check = lambda d: d.is_dir() and d.name.isdigit()
        extract = lambda f: open_read("{}/cmdline".format(f))

        systems = {
            "pulseaudio": self.__pulseaudio
        }

        reg = re.compile(r"|".join(systems.keys()))

        vol = None
        pids = (extract(i) for i in p("/proc").iterdir() if check(i))
        pids = (reg.search(i) for i in pids if i and reg.search(i))
        audio = next(pids, None)

        if audio is not None:
            vol = systems[audio.group(0)]()
            vol = _round(vol, self.options.misc_volume_round)

        return vol


    def get_scr(self):
        check = lambda f: "kbd" not in f and "backlight" in f

        scr = None
        scr_files = (f for f in p("/sys/devices").rglob("*") if check(f.name))
        scr_dir = next(scr_files, None)

        if scr_dir is not None:
            curr = int(open_read("{}/brightness".format(scr_dir)))
            max_bright = int(open_read("{}/max_brightness".format(scr_dir)))
            scr = percent(curr, max_bright)
            scr = _round(scr, self.options.misc_screen_round)

        return scr


    def __pulseaudio(self):
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
