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

# pylint: disable=too-few-public-methods

""" Sysctl module """

from functools import lru_cache

from .utils import run


class Sysctl():
    """ Sysctl class for storing sysctl variables """

    @staticmethod
    @lru_cache()
    def query(key, default=None):
        """ Fetch a sysctl variable """
        out = run(["sysctl", "-n", key])
        if out is None:
            return default

        out = out.strip()
        if not out:
            return default
        return out
