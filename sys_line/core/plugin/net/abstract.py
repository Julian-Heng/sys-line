#!/usr/bin/env python3

import time
import re

from abc import abstractmethod
from functools import lru_cache

from sys_line.core.plugin.abstract import AbstractPlugin
from sys_line.tools.storage import Storage
from sys_line.tools.utils import run


class AbstractNetwork(AbstractPlugin):
    """ Abstract network class to be implemented by subclass """

    @property
    @abstractmethod
    def _LOCAL_IP_CMD(self):
        pass

    @lru_cache(maxsize=1)
    @abstractmethod
    def dev(self, options=None):
        """ Abstract network device method to be implemented by subclass """

    @abstractmethod
    def _ssid(self):
        """ Abstract ssid resource method to be implemented by subclass """

    def ssid(self, options=None):
        """ Network ssid method """
        cmd, reg = self._ssid()
        if cmd is None or reg is None:
            return None

        out = run(cmd)
        if not out:
            return None

        ssid = (reg.match(i.strip()) for i in out.splitlines())
        ssid = next((i.group(1) for i in ssid if i), None)
        return ssid

    def local_ip(self, options=None):
        """ Network local ip method """
        dev = self.dev(options)
        if dev is None:
            return None

        reg = re.compile(r"^inet\s+((?:[0-9]{1,3}\.){3}[0-9]{1,3})")
        ip_out = run(self._LOCAL_IP_CMD + [dev])
        if not ip_out:
            return None

        ip_out = ip_out.strip().splitlines()
        ip_out = (reg.match(line.strip()) for line in ip_out)
        ip_out = next((i.group(1) for i in ip_out if i), None)
        return ip_out

    @abstractmethod
    def _bytes_delta(self, dev, mode):
        """
        Abstract network bytes delta method to fetch the change in bytes on
        a device depending on mode
        """

    def _bytes_rate(self, dev, mode):
        """
        Abstract network bytes rate method to fetch the rate of change in bytes
        on a device depending on mode
        """
        if dev is None:
            return 0.0

        start = self._bytes_delta(dev, mode)
        start_time = time.time()

        # Timeout after 2 seconds
        while (self._bytes_delta(dev, mode) <= start and
               time.time() - start_time < 2):
            time.sleep(0.01)

        end = self._bytes_delta(dev, mode)
        if end == start:
            return 0.0

        end_time = time.time()
        delta_bytes = end - start
        delta_time = end_time - start_time

        return delta_bytes / delta_time

    def download(self, options=None):
        """ Network download method """
        if options is None:
            options = self.default_options

        dev = self.dev(options)
        bytes_rate = self._bytes_rate(dev, "down")
        download = Storage(bytes_rate, prefix="B",
                           rounding=options.download.round)
        download.prefix = options.download.prefix
        return download

    def upload(self, options=None):
        """ Network upload method """
        if options is None:
            options = self.default_options

        dev = self.dev(options)
        bytes_rate = self._bytes_rate(dev, "up")
        upload = Storage(bytes_rate, prefix="B",
                         rounding=options.upload.round)
        upload.prefix = options.upload.prefix
        return upload


