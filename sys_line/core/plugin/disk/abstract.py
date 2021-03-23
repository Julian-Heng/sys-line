#!/usr/bin/env python3

import re

from abc import abstractmethod
from functools import lru_cache
from logging import getLogger
from pathlib import Path

from sys_line.core.plugin.abstract import (AbstractStoragePlugin,
                                           AbstractMultipleValuesPlugin)
from sys_line.tools.df import DfEntry
from sys_line.tools.storage import Storage
from sys_line.tools.utils import run, percent, round_trim, flatten, unique


LOG = getLogger(__name__)


class AbstractDisk(AbstractStoragePlugin, AbstractMultipleValuesPlugin):
    """ Abstract disk class to be implemented by subclass """

    def _handle_missing_option_value(self, options, info, option_name):
        if option_name not in options.query:
            options.query = tuple(list(options.query) + [option_name])

        if not Path(option_name).is_block_device():
            LOG.debug("disk index is a mount, attempting to get device...")

            dev = self._mount_to_devname(options, option_name)
            if dev is None:
                LOG.debug("unable to get device")
            else:
                LOG.debug("'%s' is '%s'", option_name, dev)
            option_name = dev

        super(AbstractDisk, self)._handle_missing_option_value(options, info,
                                                               option_name)

    def _mount_to_devname(self, options, mount_path):
        mounts = self.mount(options)
        target = next((k for k, v in mounts.items() if mount_path == v), None)
        return target

    @property
    @abstractmethod
    def _DF_FLAGS(self):
        pass

    @property
    @lru_cache(maxsize=1)
    def _df(self):
        df_out = run(self._DF_FLAGS)

        if not df_out:
            return None

        df_out = df_out.strip().splitlines()[1:]
        return df_out

    @lru_cache(maxsize=1)
    def _df_query(self, query):
        """ Return df entries """
        disks = list()
        mounts = list()

        if not query:
            LOG.debug("df query is empty, defaulting to '/'")
            mounts.append(r"/")
        else:
            for p in filter(Path.exists, map(Path, query)):
                if p.is_block_device():
                    disks.append(str(p.resolve()))
                else:
                    mounts.append(str(p.resolve()))

        reg = list()
        if disks:
            disks = r"|".join(disks)
            reg.append(fr"^({disks})")
        if mounts:
            mounts = r"|".join(mounts)
            reg.append(fr"({mounts})$")
        reg = r"|".join(reg)
        LOG.debug("df query regex is '%s'", reg)
        reg = re.compile(reg)

        results = dict()
        if self._df is None:
            LOG.debug("unable to get df output")
            return results

        for i in filter(reg.search, self._df):
            split = i.split()
            if split[0] in results.keys():
                continue

            df_entry = DfEntry(*split)
            results[df_entry.filesystem] = df_entry

        return results

    def _original_dev(self, options=None):
        """ Disk device without modification """
        if options is None:
            query = tuple()
        else:
            query = options.query

        df = self._df_query(query)
        if df is None:
            return None

        dev = {k: v.filesystem for k, v in df.items()}
        return dev

    def dev(self, options=None):
        """ Disk device method """
        if options is None:
            options = self.default_options

        dev = self._original_dev(options)

        if dev is None:
            return None

        if options.dev.short:
            dev = {k: v.split("/")[-1] for k, v in dev.items()}

        return dev

    @abstractmethod
    def name(self, options=None):
        """ Abstract disk name method to be implemented by subclass """

    def mount(self, options=None):
        """ Disk mount method """
        if options is None:
            query = tuple()
        else:
            query = options.query

        df = self._df_query(query)
        if df is None:
            return None

        mount = {k: v.mount for k, v in df.items()}
        return mount

    @abstractmethod
    def partition(self, options=None):
        """ Abstract disk partition method to be implemented by subclass """

    def _used(self):
        pass

    def used(self, options=None):
        """ Disk used method """
        if options is None:
            options = self.default_options
            query = tuple()
        else:
            query = options.query

        df = self._df_query(query)
        if df is None:
            return None

        used = dict()
        for k, v in df.items():
            stor = Storage(int(v.used), prefix="KiB",
                           rounding=options.used.round)
            stor.prefix = options.used.prefix
            used[k] = stor

        return used

    def _total(self):
        pass

    def total(self, options=None):
        """ Disk total method """
        if options is None:
            options = self.default_options
            query = tuple()
        else:
            query = options.query

        df = self._df_query(query)
        if df is None:
            return None

        total = dict()
        for k, v in df.items():
            stor = Storage(int(v.blocks), prefix="KiB",
                           rounding=options.total.round)
            stor.prefix = options.total.prefix
            total[k] = stor

        return total

    def percent(self, options=None):
        """ Disk percent property """
        if options is None:
            options = self.default_options

        devs = self._original_dev(options)
        if devs is None:
            return None

        perc = dict()
        used = self.used(options)
        total = self.total(options)

        for dev in devs.keys():
            value = percent(used[dev].bytes, total[dev].bytes)
            if value is None:
                value = 0.0
            else:
                value = round_trim(value, options.percent.round)
            perc[dev] = value

        return perc

    @staticmethod
    def _add_arguments(parser):
        parser.add_argument("-dp", "--disk-prefix", action="store",
                            default=None, choices=Storage.PREFIXES,
                            metavar="prefix", dest="disk.prefix")
        parser.add_argument("-dr", "--disk-round", action="store", type=int,
                            default=None, metavar="int", dest="disk.round")
        parser.add_argument("-dd", "--disk", nargs="+", action="append",
                            default=[], metavar="disk", dest="disk.query")
        parser.add_argument("-dm", "--mount", nargs="+", action="append",
                            default=[], metavar="mount", dest="disk.query")
        parser.add_argument("-dds", "--disk-dev-short", action="store_true",
                            default=False, dest="disk.dev.short")
        parser.add_argument("-dup", "--disk-used-prefix", action="store",
                            default="GiB", choices=Storage.PREFIXES,
                            metavar="prefix", dest="disk.used.prefix")
        parser.add_argument("-dtp", "--disk-total-prefix", action="store",
                            default="GiB", choices=Storage.PREFIXES,
                            metavar="prefix", dest="disk.total.prefix")
        parser.add_argument("-dur", "--disk-used-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="disk.used.round")
        parser.add_argument("-dtr", "--disk-total-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="disk.total.round")
        parser.add_argument("-dpr", "--disk-percent-round", action="store",
                            type=int, default=2, metavar="int",
                            dest="disk.percent.round")

    @staticmethod
    def _post_argument_parse_hook(plugin_options):
        plugin_options = (
            super(AbstractDisk, AbstractDisk)._post_argument_parse_hook(
                plugin_options
            )
        )

        plugin_options.query = (
            tuple(unique(flatten(plugin_options.query)))
        )

        return plugin_options
