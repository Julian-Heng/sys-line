#!/usr/bin/env python3


""" FreeBSD specific module """

import re
import time

from ..abstract import (System,
                        AbstractCpu)
from ..utils import run


class FreeBSD(System):
    """
    A FreeBSD implementation of the abstract
    System class in abstract.py
    """

    def __init__(self, os_name, options):
        domains = {
            "cpu": Cpu
        }

        super(FreeBSD, self).__init__(domains, os_name, options)


class Cpu(AbstractCpu):
    """ FreeBSD implementation of AbstractCpu class """

    def get_cores(self):
        return int(run(["sysctl", "-n", "hw.ncpu"]))


    def _get_cpu_speed(self):
        cpu, speed = run(["sysctl", "-n", "hw.model",
                          "hw.cpuspeed", "hw.clockrate"]).strip().split("\n")
        return cpu, int(speed) / 1000


    def get_load_avg(self):
        load = run(["sysctl", "-n", "vm.loadavg"]).split()
        return load[1] if self.options.cpu_load_short else " ".join(load[1:4])


    def get_fan(self):
        """ Stub """


    def get_temp(self):
        return float(run(["sysctl", "-n", "dev.cpu.0.temperature"])[:-2])


    def _get_uptime_sec(self):
        cmd = ["sysctl", "-n", "kern.boottime"]
        regex = r"sec = (\d+),"
        sec = int(re.search(regex, run(cmd)).group(1))

        return int(time.time()) - sec
