#!/usr/bin/env python3

import os

from abc import ABC, abstractmethod
from importlib import import_module
from logging import getLogger, DEBUG

from sys_line.core.plugin import cpu
from sys_line.core.plugin import mem
from sys_line.core.plugin import swap
from sys_line.core.plugin import disk
from sys_line.core.plugin import bat
from sys_line.core.plugin import net
from sys_line.core.plugin import date
from sys_line.core.plugin import wm
from sys_line.core.plugin import misc


LOG = getLogger(__name__)


class System(ABC):

    def __init__(self, default_options, **kwargs):
        super(System, self).__init__()

        if LOG.isEnabledFor(DEBUG):
            msg = "Initialising System with: %s"
            sys_debug = {k: f"{v.__module__}.{v.__name__}"
                         for k, v in kwargs.items()}
            LOG.debug(msg, sys_debug)

        self.plugins = dict(kwargs)
        self.default_options = {
            k: getattr(default_options, k, None) for k in self.plugins
        }
        self.plugins_cache = {k: None for k in self.plugins}

    def query(self, domain):
        """ Queries a system for a domain and info """
        LOG.debug("querying system for domain '%s'", domain)

        if domain not in self.plugins.keys():
            msg = f"domain name '{domain}' not in system"
            raise RuntimeError(msg)

        if self.plugins_cache[domain] is None:
            LOG.debug("domain '%s' is not initialised. Initialising...",
                      domain)
            opts = self.default_options[domain]
            self.plugins_cache[domain] = self.plugins[domain](domain, opts)

        return self.plugins_cache[domain]

    @staticmethod
    def create_instance(default_options, plugins):
        return System(default_options, **plugins)
