#!/usr/bin/env python3


from sys_line.core.plugin.swap.abstract import AbstractSwap
from sys_line.tools.utils import linux_mem_file


class Swap(AbstractSwap):
    """ A self implementation of the AbstractSwap class """

    def _used(self):
        mem_file = linux_mem_file()
        used = mem_file.get("SwapTotal", 0) - mem_file.get("SwapFree", 0)
        return used, "KiB"

    def _total(self):
        return linux_mem_file().get("SwapTotal", 0), "KiB"
