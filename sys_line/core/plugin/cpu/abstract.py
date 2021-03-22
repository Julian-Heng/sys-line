#!/usr/bin/env python3

import re

from abc import abstractmethod
from logging import getLogger

from sys_line.core.plugin.abstract import AbstractPlugin
from sys_line.tools.utils import round_trim, run, unix_epoch_to_str


LOG = getLogger(__name__)


class AbstractCpu(AbstractPlugin):
    """ Abstract cpu class to be implemented by subclass """

    @abstractmethod
    def cores(self, options=None):
        """ Abstract cores method to be implemented by subclass """

    @abstractmethod
    def _cpu_string(self):
        """
        Private abstract cpu string method to be implemented by subclass
        """

    @abstractmethod
    def _cpu_speed(self):
        """
        Private abstract cpu speed method to be implemented by subclass
        """

    def cpu(self, options=None):
        """ Returns cpu string """
        cpu_reg = re.compile(r"\s+@\s+(\d+\.)?\d+GHz")
        trim_reg = re.compile(r"CPU|\((R|TM)\)")

        cores = self.cores(options)
        cpu = self._cpu_string()
        speed = self._cpu_speed()
        cpu = trim_reg.sub("", cpu.strip())

        if speed is not None:
            fmt = fr" ({cores}) @ {speed}GHz"
            cpu = cpu_reg.sub(fmt, cpu)
        else:
            LOG.debug("unable to get cpu speed, using fallback speed")
            fmt = fr"({cores}) @"
            cpu = re.sub(r"@", fmt, cpu)

        cpu = re.sub(r"\s+", " ", cpu)
        return cpu

    @abstractmethod
    def _load_avg(self):
        """ Abstract load average method to be implemented by subclass """

    def load_avg(self, options=None):
        """ Load average method """
        if options is None:
            options = self.default_options

        load = self._load_avg()
        if load is None:
            LOG.debug("unable to get load")
            return None

        if options.load_avg.short:
            return load[0]

        return " ".join(load)

    def cpu_usage(self, options=None):
        """ Cpu usage method """
        if options is None:
            options = self.default_options

        cores = self.cores(options)
        ps_cmd = ["ps", "-e", "-o", "%cpu"]
        ps_out = run(ps_cmd)

        if not ps_out:
            LOG.debug("unable to get ps output")
            return None

        ps_out = ps_out.strip().splitlines()[1:]
        cpu_usage = sum(map(float, ps_out)) / cores
        cpu_usage = round_trim(cpu_usage, options.cpu_usage.round)
        return cpu_usage

    @abstractmethod
    def fan(self, options=None):
        """ Abstract fan method to be implemented by subclass """

    @abstractmethod
    def _temp(self):
        """ Abstract temperature method to be implemented by subclass """

    def temp(self, options=None):
        """ Temperature method """
        if options is None:
            options = self.default_options

        temp = self._temp()
        if temp is None:
            LOG.debug("unable to get temp output")
            return None

        temp = round_trim(temp, options.temp.round)
        return temp

    @abstractmethod
    def _uptime(self):
        """ Abstract uptime method to be implemented by subclass """

    def uptime(self, options=None):
        """ Uptime method """
        uptime = self._uptime()
        if uptime is None:
            LOG.debug("unable to get uptime")
            return None

        uptime = unix_epoch_to_str(uptime)
        return uptime
