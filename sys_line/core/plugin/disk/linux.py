#!/usr/bin/env python3

import re
import shlex

from functools import lru_cache

from sys_line.core.plugin.disk.abstract import AbstractDisk
from sys_line.tools.utils import run, which


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
        lsblk_exe = which("lsblk")
        if not lsblk_exe:
            LOG.debug("unable to find lsblk binary")
            return None

        columns = ["NAME", "LABEL", "PARTLABEL", "FSTYPE"]
        cmd = [lsblk_exe, "--output", ",".join(columns), "--paths", "--pairs"]
        lsblk_out = run(cmd)
        if not lsblk_out:
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
            LOG.debug("unable to get disk devices")
            return None

        lsblk_entries = self._lsblk_entries
        if lsblk_entries is None:
            LOG.debug("unable to get output from lsblk")
            return {k: None for k in devs.keys()}

        labels = ["LABEL", "PARTLABEL"]
        names = {k: next((v[i] for i in labels if v[i]), None)
                 for k, v in lsblk_entries.items() if k in devs}
        return names

    def partition(self, options=None):
        devs = self._original_dev(options)
        if devs is None:
            LOG.debug("unable to get disk devices")
            return None

        lsblk_entries = self._lsblk_entries
        if lsblk_entries is None:
            LOG.debug("unable to get output from lsblk")
            return {k: None for k in devs.keys()}

        partitions = {k: v["FSTYPE"]
                      for k, v in lsblk_entries.items() if k in devs}
        return partitions
