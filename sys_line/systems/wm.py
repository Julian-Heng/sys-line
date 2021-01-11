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

from logging import getLogger
from types import SimpleNamespace

from .abstract import AbstractWindowManager
from ..tools.utils import run, trim_string, which


LOG = getLogger(__name__)


class Yabai(AbstractWindowManager):
    """ Yabai window manager implementation """

    def desktop_index(self, options=None):
        query = Yabai._yabai_query("--spaces", "--space")
        if query is None:
            LOG.debug("unable to query yabai for desktop index")
            return None

        return query.index

    def desktop_name(self, options=None):
        index = self.desktop_index(options)
        if index is None:
            LOG.debug("unable to query yabai for desktop name")
            return None

        return f"Desktop {index}"

    def app_name(self, options=None):
        query = Yabai._yabai_query("--windows", "--window")
        if query is None:
            LOG.debug("unable to query yabai for application name")
            return None

        return query.app

    def window_name(self, options=None):
        query = Yabai._yabai_query("--windows", "--window")
        if query is None:
            LOG.debug("unable to query yabai for window name")
            return None

        return query.title

    @staticmethod
    def _yabai_query(*args):
        """ Returns an object of the json respose from the query """
        yabai_exe = which("yabai")
        if not yabai_exe:
            LOG.debug("unable to find yabai binary")

        if not args:
            LOG.debug("no arguments are provided")
            return None

        result = run([yabai_exe, "-m", "query"] + list(args))
        if not result:
            return None

        result = json.loads(result, object_hook=lambda d: SimpleNamespace(**d))
        return result


class Xorg(AbstractWindowManager):
    """ Xorg window managers implementation """

    def desktop_index(self, options=None):
        current_desktop = Xorg._xprop_query("0c", "_NET_CURRENT_DESKTOP")
        if current_desktop is None:
            LOG.debug("unable to query xprop for desktop index")
            return None

        index = current_desktop[-1]
        return index

    def desktop_name(self, options=None):
        index = self.desktop_index(options)
        desktops = Xorg._xprop_query("8u", "_NET_DESKTOP_NAMES")

        if index is None:
            LOG.debug("index is not valid, unable to get desktop name")
            return None

        if desktops is None:
            LOG.debug("unable to query xprop for desktop names")
            return None

        try:
            name = desktops[int(index)]
        except IndexError:
            LOG.debug(
                "index is not valid, getting first available desktop name"
            )
            name = next(iter(desktops), None)

        return name

    def app_name(self, options=None):
        window_id = Xorg._current_window_id()
        if window_id is None:
            LOG.debug("unable to get window id")
            return None

        name = Xorg._xprop_query("8s", "WM_CLASS", window_id=window_id)
        if name is None:
            LOG.debug("unable to query xprop for application name")
            return None

        name = name[-1]
        return name

    def window_name(self, options=None):
        window_id = Xorg._current_window_id()

        if window_id is None:
            LOG.debug("unable to get window id")
            return None

        name = Xorg._xprop_query("8s", "WM_NAME", window_id=window_id)
        if name is None:
            return None

        name = name[-1]
        return name

    @staticmethod
    def _current_window_id():
        xprop_exe = which("xprop")
        if not xprop_exe:
            return None

        cmd = [
            xprop_exe, "-root", "-notype", "32x", r"\n$0",
            "_NET_ACTIVE_WINDOW"
        ]

        out = run(cmd)
        if not out or "not found" in out:
            return None

        window_id = out.split("\n")[-1]

        return window_id

    @staticmethod
    def _xprop_query(fmt, prop, window_id=None):
        xprop_exe = which("xprop")
        if not xprop_exe:
            return None

        if window_id is None:
            cmd = [xprop_exe, "-root", "-notype", fmt, r"\n$0+", prop]
        else:
            cmd = [xprop_exe, "-notype", "-id", window_id, fmt,
                   r"\n$0+", prop]

        out = run(cmd)
        if not out or "not found" in out:
            return None

        out = out.split("\n")[-1]
        out = shlex.split(out)
        out = [trim_string(i.rstrip(",")) for i in out]

        return out
