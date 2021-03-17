#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2021  Julian Heng
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

# pylint: disable=too-many-arguments

""" df model class """


class DfEntry():
    """ DfEntry class to store the columns for a line in the output of 'df' """

    def __init__(self, filesystem, blocks, used, available, percent, mount):
        self._filesystem = filesystem
        self._blocks = blocks
        self._used = used
        self._available = available
        self._percent = percent
        self._mount = mount

    @property
    def filesystem(self):
        """ Returns the value under the 'filesystem' column """
        return self._filesystem

    @property
    def blocks(self):
        """ Returns the value under the 'blocks' column """
        return self._blocks

    @property
    def used(self):
        """ Returns the value under the 'used' column """
        return self._used

    @property
    def available(self):
        """ Returns the value under the 'available' column """
        return self._available

    @property
    def percent(self):
        """ Returns the value under the 'percent' column """
        return self._percent

    @property
    def mount(self):
        """ Returns the value under the 'mount' column """
        return self._mount
