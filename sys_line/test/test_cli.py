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

from types import SimpleNamespace

from ..tools.cli import flatten, unique, dict_to_namespace


class TestFlatten(unittest.TestCase):

    def test__cli_flatten(self):
        self.assertEqual(flatten(["a"]), ["a"])
        self.assertEqual(flatten(["a", ["a"]]), ["a", "a"])


class TestUnique(unittest.TestCase):

    def test__cli_unique(self):
        self.assertEqual(unique([""]), [""])
        self.assertEqual(unique(["a"]), ["a"])
        self.assertEqual(unique(["a", "b"]), ["a", "b"])
        self.assertEqual(unique(["a", "b", "a"]), ["a", "b"])


class TestDictToNamespace(unittest.TestCase):

    def test__cli_dict_to_namespace(self):
        def validate(nspace, attr_dict):
            self.assertEqual(isinstance(nspace, SimpleNamespace), True)
            for key in attr_dict.keys():
                self.assertEqual(hasattr(nspace, key), True)
                value = getattr(nspace, key)
                if isinstance(value, SimpleNamespace):
                    validate(value, attr_dict[key])
                else:
                    self.assertEqual(value, attr_dict[key])

        inputs = [
            {},
            {"a": "b"},
            {"a": {"b": "c"}},
            {"x": {"a": {"b": "c"}, "d": ["e", "f"]}, "y": ("z")},
        ]

        for i in inputs:
            validate(dict_to_namespace(i), i)
