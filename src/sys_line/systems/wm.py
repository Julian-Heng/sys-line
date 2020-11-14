#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2020  Julian Heng
#
# This file is part of sys-line.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" Window manager implementations """

import json
import shlex
import shutil

from functools import lru_cache
from types import SimpleNamespace

from .abstract import AbstractWindowManager
from ..tools.utils import run, trim_string


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
        if not result:
            return None

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


class Xorg(AbstractWindowManager):
    """ Xorg window managers implementation """

    @property
    @lru_cache(maxsize=1)
    def _xprop_exe(self):
        """ Returns the path to the yabai executable """
        return shutil.which("xprop")

    @property
    def _current_window_id(self):
        if not self._xprop_exe:
            return None

        window_id = run(
            [self._xprop_exe, "-root", "32x", r"\t$0", "_NET_ACTIVE_WINDOW"]
        ).split()[1]
        return window_id

    def _xprop_query(self, prop, window_id=None):
        if not self._xprop_exe:
            return None

        if window_id is None:
            cmd = [self._xprop_exe, "-root", "-notype", prop]
        else:
            cmd = [self._xprop_exe, "-id", window_id, prop]

        result = run(cmd).strip().split("\n")

        if not result:
            return None

        if len(result) > 1:
            result = list(map(trim_string, result[1:]))
        else:
            result = result[0]

            if " = " in result:
                result = result.split(" = ")[-1]
            elif ":" in result:
                result = result.split(":")[-1]

            if "not found" in result:
                result = None
            else:
                result = shlex.split(result)
                result = [trim_string(i.rstrip(",")) for i in result]

        if result is not None and len(result) == 1:
            result = result[0]

        return result

    @property
    def desktop_index(self):
        index = self._xprop_query("_NET_CURRENT_DESKTOP")
        return index

    @property
    def desktop_name(self):
        index = self.desktop_index
        desktops = self._xprop_query("_NET_DESKTOP_NAMES")
        name = desktops[int(index)]
        return name

    @property
    def app_name(self):
        window_id = self._current_window_id
        name = self._xprop_query("WM_CLASS", window_id=window_id)
        if len(name) > 0:
            name = name[0]
        return name

    @property
    def window_name(self):
        window_id = self._current_window_id
        name = self._xprop_query("WM_NAME", window_id=window_id)
        if not name:
            name = None
        return name
