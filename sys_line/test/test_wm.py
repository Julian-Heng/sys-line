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

import unittest

from unittest.mock import MagicMock, PropertyMock, patch

from ..systems.wm import Yabai
from ..tools.utils import which


class TestYabai(unittest.TestCase):

    def setUp(self):
        super(TestYabai, self).setUp()

        self.wm = Yabai("wm", None)
        self.which_patch = patch("shutil.which").start()
        self.run_patch = patch("sys_line.systems.wm.run").start()
        which.cache_clear()

        self.yabai_exe = "/usr/local/bin/yabai"
        self.query_spaces_out = """{
	"id":3,
	"label":"",
	"index":1,
	"display":1,
	"windows":[52, 1263],
	"type":"bsp",
	"visible":1,
	"focused":1,
	"native-fullscreen":0,
	"first-window":52,
	"last-window":52
}
"""

        self.query_windows_out = """{
	"id":52,
	"pid":543,
	"app":"iTerm2",
	"title":"[0] bash: Julians-MBP",
	"frame":{
		"x":4.0000,
		"y":4.0000,
		"w":1672.0000,
		"h":1022.0000
	},
	"level":0,
	"role":"AXWindow",
	"subrole":"AXStandardWindow",
	"movable":1,
	"resizable":1,
	"display":1,
	"space":1,
	"visible":1,
	"focused":1,
	"split":"none",
	"floating":0,
	"sticky":0,
	"minimized":0,
	"topmost":0,
	"opacity":1.0000,
	"shadow":0,
	"border":1,
	"stack-index":0,
	"zoom-parent":0,
	"zoom-fullscreen":0,
	"native-fullscreen":0
}
"""

    def tearDown(self):
        super(TestYabai, self).tearDown()
        patch.stopall()

    def test__yabai_desktop_index_valid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = self.query_spaces_out

        self.assertEqual(self.wm.desktop_index(), 1)

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--spaces", "--space"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_desktop_name_valid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = self.query_spaces_out

        self.assertEqual(self.wm.desktop_name(), "Desktop 1")

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--spaces", "--space"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_app_name_valid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = self.query_windows_out

        self.assertEqual(self.wm.app_name(), "iTerm2")

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--windows",
            "--window"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_window_name_valid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = self.query_windows_out

        self.assertEqual(self.wm.window_name(), "[0] bash: Julians-MBP")

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--windows",
            "--window"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_desktop_index_invalid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = ""

        self.assertEqual(self.wm.desktop_index(), None)

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--spaces", "--space"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_desktop_name_invalid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = ""

        self.assertEqual(self.wm.desktop_name(), None)

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--spaces", "--space"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_app_name_invalid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = ""

        self.assertEqual(self.wm.app_name(), None)

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--windows",
            "--window"
        ]
        self.assertEqual(args, (expected,))

    def test__yabai_window_name_invalid(self):
        self.which_patch.return_value = self.yabai_exe
        self.run_patch.return_value = ""

        self.assertEqual(self.wm.window_name(), None)

        args, _ = self.which_patch.call_args
        self.assertEqual(args, ("yabai",))

        args, _ = self.run_patch.call_args
        expected = [
            self.which_patch.return_value, "-m", "query", "--windows",
            "--window"
        ]
        self.assertEqual(args, (expected,))
