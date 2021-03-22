#!/usr/bin/env python3

from sys_line.core.plugin.mem.abstract import AbstractMemory
from sys_line.tools.storage import Storage
from sys_line.tools.utils import linux_mem_file


class Memory(AbstractMemory):
    """ A Linux implementation of the AbstractMemory class """

    def _used(self):
        mem_file = linux_mem_file()
        keys = [["MemTotal", "Shmem"],
                ["MemFree", "Buffers", "Cached", "SReclaimable"]]
        used = sum(mem_file.get(i, 0) for i in keys[0])
        used -= sum(mem_file.get(i, 0) for i in keys[1])
        return used, "KiB"

    def _total(self):
        return linux_mem_file().get("MemTotal", 0), "KiB"
