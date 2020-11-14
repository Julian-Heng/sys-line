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

import unittest
from ..tools.utils import (percent, run, unix_epoch_to_str, round_trim,
                           trim_string)


class TestPercent(unittest.TestCase):

    def test__utils_percent_valid(self):
        self.assertEqual(percent(1, 2), 50.0)
        self.assertEqual(percent(-1, 2), -50.0)
        self.assertAlmostEqual(percent(1, 3), 33.33, places=2)

    def test__utils_percent_zero(self):
        self.assertEqual(percent(1, 0), None)


class TestRun(unittest.TestCase):

    def test__utils_run(self):
        self.assertEqual(run(["echo", "asdf"]), "asdf\n")


class TestUnixEpochToString(unittest.TestCase):

    def test__utils_unix_epoch_to_string(self):
        self.assertEqual(unix_epoch_to_str(0), None)
        self.assertEqual(unix_epoch_to_str(1), "1s")
        self.assertEqual(unix_epoch_to_str(60), "1m")
        self.assertEqual(unix_epoch_to_str(3600), "1h")
        self.assertEqual(unix_epoch_to_str(86400), "1d")
        self.assertEqual(unix_epoch_to_str(86400 + 3600), "1d 1h")
        self.assertEqual(unix_epoch_to_str(86400 + 3600 + 60),
                         "1d 1h 1m")
        self.assertEqual(unix_epoch_to_str(86400 + 3600 + 60 + 1),
                         "1d 1h 1m 1s")


class TestRoundTrim(unittest.TestCase):

    def test__utils_round_trim_valid(self):
        self.assertEqual(round_trim(11.111, 1), 11.1)
        self.assertEqual(round_trim(11.111, 0), 11)
        self.assertEqual(round_trim(11.0, 1), 11)
        self.assertEqual(round_trim(11.0, 0), 11)
        self.assertEqual(round_trim(11, 0), 11)

        self.assertEqual(round_trim(11.91, 1), 11.9)
        self.assertEqual(round_trim(11.999, 1), 12)
        self.assertEqual(round_trim(11.999, 0), 12)


class TestTrimString(unittest.TestCase):

    def test__utils_trim_string(self):
        self.assertEqual(trim_string(""), "")
        self.assertEqual(trim_string(" "), "")
        self.assertEqual(trim_string(" a"), "a")
        self.assertEqual(trim_string("a "), "a")
        self.assertEqual(trim_string(" a "), "a")
        self.assertEqual(trim_string(" a b  c  d  e   f"), "a b c d e f")
