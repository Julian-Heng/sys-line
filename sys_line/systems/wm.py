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

    def desktop_index(self, options=None):
        query = self._yabai_query("--spaces", "--space")
        return query.index if query is not None else None

    def desktop_name(self, options=None):
        index = self.desktop_index(options)
        return f"Desktop {index}" if index is not None else None

    def app_name(self, options=None):
        query = self._yabai_query("--windows", "--window")
        return query.app if query is not None else None

    def window_name(self, options=None):
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

        out = run([
            self._xprop_exe, "-root", "-notype", "32x", r"\n$0",
            "_NET_ACTIVE_WINDOW"
        ])

        if not out or "not found" in out:
            return None

        window_id = out.split("\n")[-1]

        return window_id

    def _xprop_query(self, fmt, prop, window_id=None):
        if not self._xprop_exe:
            return None

        if window_id is None:
            cmd = [self._xprop_exe, "-root", "-notype", fmt, "\n$0+", prop]
        else:
            cmd = [self._xprop_exe, "-notype", "-id", window_id, fmt, "\n$0+",
                   prop]

        out = run(cmd)

        if not out or "not found" in out:
            return None

        out = out.split("\n")[-1]
        out = shlex.split(out)
        out = [trim_string(i.rstrip(",")) for i in out]

        return out

    def desktop_index(self, options=None):
        current_desktop = self._xprop_query("0c", "_NET_CURRENT_DESKTOP")
        if current_desktop is None:
            return None

        index = current_desktop[-1]
        return index

    def desktop_name(self, options=None):
        name = None
        index = self.desktop_index(options)
        desktops = self._xprop_query("8u", "_NET_DESKTOP_NAMES")

        if index is not None and desktops is not None:
            try:
                name = desktops[int(index)]
            except IndexError:
                name = next(iter(desktops))

        return name

    def app_name(self, options=None):
        name = None
        window_id = self._current_window_id

        if window_id is not None:
            name = self._xprop_query("8s", "WM_CLASS", window_id=window_id)
            if name is not None:
                name = name[-1]

        return name

    def window_name(self, options=None):
        name = None
        window_id = self._current_window_id

        if window_id is not None:
            name = self._xprop_query("8s", "WM_NAME", window_id=window_id)
            if name is not None:
                name = name[-1]

        return name
