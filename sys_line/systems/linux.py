#!/usr/bin/env python3
# pylint: disable=no-self-use

""" Linux specific module """

import re
import shutil

from pathlib import Path as p

from sys_line.abstract import (System,
                               AbstractCpu,
                               AbstractMemory,
                               AbstractSwap,
                               AbstractDisk,
                               AbstractBattery,
                               AbstractNetwork,
                               AbstractMisc)
from sys_line.storage import Storage
from sys_line.utils import open_read, run, percent


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
            "bat": Battery,
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
        check = lambda f: int(open_read(f)) != 0

        fan = None
        fan_dir = "/sys/devices/platform"
        glob = "fan1_input"
        files = (f for f in p(fan_dir).rglob(glob) if check(f))

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
                       rounding=self.options.mem_used_round)
        used.set_prefix(self.options.mem_used_prefix)
        return used


    def get_total(self):
        total = Storage(int(self.mem_file["SwapTotal"]), prefix="KiB",
                        rounding=self.options.mem_total_round)

        total.set_prefix(self.options.mem_total_prefix)
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


class Battery(AbstractBattery):
    """ Linux implementation of AbstractBattery class """

    def get_is_present(self):
        pass


    def get_is_charging(self):
        pass


    def get_is_full(self):
        pass


    def get_percent(self):
        pass


    def _get_time(self):
        pass


    def get_power(self):
        pass


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
                    regex = "^SSID: (.*)$"

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
        pids = [extract(i) for i in p("/proc").iterdir() if check(i)]
        pids = (reg.search(i) for i in pids if i and reg.search(i))
        audio = next(pids, None)

        if audio is not None:
            vol = systems[audio.group(0)]()

        return round(vol, self.options.misc_volume_round)


    def get_scr(self):
        pass


    def __pulseaudio(self):
        default_reg = re.compile(r"^set-default-sink (.*)$", re.M)
        pac_dump = run(["pacmd", "dump"])

        vol = None
        default = default_reg.search(pac_dump)
        if default is not None:
            vol_reg = r"^set-sink-volume {} 0x(.*)$".format(default.group(1))
            vol_reg = re.compile(vol_reg, re.M)
            vol = vol_reg.search(pac_dump)
            if vol is not None:
                vol = percent(int(vol.group(1), 16), pow(2, 16))

        return vol
