#!/usr/bin/env python3

from abc import abstractmethod

from sys_line.core.plugin.abstract import AbstractPlugin
from sys_line.tools.utils import run


class AbstractWindowManager(AbstractPlugin):
    """ Abstract window manager class to be implemented by subclass """

    """
    @staticmethod
    def _post_import_hook(plugin):
        ps_out = run(["ps", "ax", "-e", "-o", "command"])

        if not ps_out:
            return WindowManagerStub

        avail = (v for k, v in plugin._SUPPORTED_WMS().items() if k in ps_out)
        return next(avail, WindowManagerStub)
        """
    @staticmethod
    def _detect_window_manager(wms):
        ps_out = run(["ps", "ax", "-e", "-o", "command"])

        if not ps_out:
            return WindowManagerStub

        return next((v for k, v in wms.items() if k in ps_out),
                    WindowManagerStub)

    @abstractmethod
    def desktop_index(self, options=None):
        """ Abstract desktop index method to be implemented by subclass """

    @abstractmethod
    def desktop_name(self, options=None):
        """ Abstract desktop name method to be implemented by subclass """

    @abstractmethod
    def app_name(self, options=None):
        """
        Abstract focused application name method to be implemented by subclass
        """

    @abstractmethod
    def window_name(self, options=None):
        """
        Abstract focused window name method to be implemented by subclass
        """


class WindowManagerStub(AbstractWindowManager):
    """ Placeholder window manager """

    def desktop_index(self, options=None):
        return None

    def desktop_name(self, options=None):
        return None

    def app_name(self, options=None):
        return None

    def window_name(self, options=None):
        return None
