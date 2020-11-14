#!/usr/bin/env python3

""" Window manager implementations """

import json
import shutil

from functools import lru_cache
from types import SimpleNamespace

from .abstract import AbstractWindowManager
from ..tools.utils import run


class Yabai(AbstractWindowManager):
    """ Yabai window manager implementation """

    @property
    @lru_cache(maxsize=1)
    def _yabai_exe(self):
        """ Returns the path to the yabai executable """
        return shutil.which("yabai")

    def _yabai_query(self, *args):
        """ Returns an object of the json respose from the query """
        if not self._yabai_exe or not args:
            return None

        result = run([self._yabai_exe, "-m", "query"] + list(args))
        result = json.loads(result, object_hook=lambda d: SimpleNamespace(**d))
        return result

    @property
    def desktop_index(self):
        query = self._yabai_query("--spaces", "--space")
        return query.index if query is not None else None

    @property
    def desktop_name(self):
        index = self.desktop_index
        return f"Desktop {index}" if index is not None else None

    @property
    def app_name(self):
        query = self._yabai_query("--windows", "--window")
        return query.app if query is not None else None

    @property
    def window_name(self):
        query = self._yabai_query("--windows", "--window")
        return query.title if query is not None else None


class WindowManagerStub(AbstractWindowManager):
    """ Placeholder window manager """

    @property
    def desktop_index(self):
        return None

    @property
    def desktop_name(self):
        return None

    @property
    def app_name(self):
        return None

    @property
    def window_name(self):
        return None
