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
