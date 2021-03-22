#!/usr/bin/env python3

import re

from pathlib import Path
from logging import getLogger
from functools import lru_cache

from sys_line.core.plugin.cpu.abstract import AbstractCpu
from sys_line.tools.utils import open_read, round_trim


LOG = getLogger(__name__)


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
            LOG.debug("unable to match cpu regex")
            return None

        cpu = match.group(1)
        return cpu

    def _cpu_speed(self):
        speed_path = self._cpu_speed_file_path
        if speed_path is None:
            LOG.debug("unable to find cpu speed file")
            return None

        speed = open_read(speed_path)
        if speed is None or not speed.strip().isnumeric():
            LOG.debug("unable to read cpu speed file '%s'", speed_path)
            return None

        speed = round_trim(float(speed) / 1e6, 2)
        return speed

    def _load_avg(self):
        load_path = Cpu._FILES["proc_load"]
        load_file = open_read(load_path)
        if load_file is None:
            LOG.debug("unable to read loadavg file '%s'", load_path)
            return None

        load = load_file.strip().split()[:3]
        return load

    def fan(self, options=None):
        fan_path = self._cpu_fan_file_path
        if fan_path is None:
            LOG.debug("unable to find fan file")
            return None

        fan = open_read(fan_path)
        if fan is None or not fan.strip().isnumeric():
            LOG.debug("unable to read fan file '%s'", fan_path)
            return None

        fan = int(fan.strip())
        return fan

    def _temp(self):
        temp_paths = self._cpu_temp_file_paths
        if not temp_paths:
            LOG.debug("unable to find temperature directory")
            return None

        temp_path = next(iter(temp_paths))
        temp = open_read(temp_path)
        if temp is None:
            LOG.debug("unable to read temperature file '%s'", temp_path)
            return None

        temp = float(temp) / 1000
        return temp

    def _uptime(self):
        uptime = None
        uptime_path = Cpu._FILES["proc_uptime"]
        uptime_file = open_read(uptime_path)
        if uptime_file is None:
            LOG.debug("unable to read uptime file '%s'", uptime_path)
            return None

        uptime = int(float(uptime_file.strip().split(" ")[0]))
        return uptime
