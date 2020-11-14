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

from unittest.mock import MagicMock

from ..tools.format import FormatTree, FormatInfo, Tokenizer


class TestTokenizer(unittest.TestCase):

    def test__tokenizer(self):
        inputs = [
            ("", []),
            ("a", ["a"]),
            ("a b", ["a b"]),
            ("a {a.b}", ["a ", "{a.b}"]),
            ("a {a.b?{c.d}}", ["a ", "{a.b?{c.d}}"]),
            ("a {a.b[z]?{c.d}}", ["a ", "{a.b[z]?{c.d}}"]),
            ("a {a.b} {c.d}", ["a ", "{a.b}", " ", "{c.d}"])
        ]

        for i in inputs:
            string, expected = i
            self.assertEqual(Tokenizer.tokenize(string), expected)


class TestFormatBase(unittest.TestCase):

    def setUp(self):
        self.system_mock = MagicMock()
        self.test_mock_a = MagicMock()
        self.test_mock_c = MagicMock()


class TestFormatTree(TestFormatBase):

    def test__format_tree_contructor_empty(self):
        ft = FormatTree(self.system_mock, "")
        self.assertEqual(ft.system, self.system_mock)
        self.assertEqual(ft.fmt, "")
        self.assertEqual(ft.tokens, [])

    def test__format_tree_contructor_string(self):
        string = "this is a string"
        ft = FormatTree(self.system_mock, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, [string])

    def test__format_tree_contructor_string_info(self):
        string = "this has info {a.b}"
        ft = FormatTree(self.system_mock, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, ["this has info ", "{a.b}"])

    def test__format_tree_build(self):
        self.test_mock_a.query.return_value = "a_b"
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatTree(self.system_mock, "| {a.b} |")
        self.assertEqual(ft.build(), "| a_b |")

    def test__format_tree_build_invalid(self):
        self.test_mock_a.query.return_value = False
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatTree(self.system_mock, "| {a.b} |")
        self.assertEqual(ft.build(), "|  |")

    def test__format_tree_build_invalid_with_alt(self):
        self.test_mock_a.query.return_value = False
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatTree(self.system_mock, "| {a.b?sub} |")
        self.assertEqual(ft.build(), "|  |")

    def test__format_tree_build_valid_with_alt(self):
        self.test_mock_a.query.return_value = True
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatTree(self.system_mock, "| {a.b?sub} |")
        self.assertEqual(ft.build(), "| sub |")

    def test__format_tree_build_multiple_info(self):
        self.test_mock_a.query.return_value = "a_b"
        self.test_mock_c.query.return_value = "c_d"
        self.system_mock.query.side_effect = [self.test_mock_a,
                                              self.test_mock_c]
        ft = FormatTree(self.system_mock, "| {a.b?a: {}, c: {c.d}} |")
        self.assertEqual(ft.build(), "| a: a_b, c: c_d |")


class TestFormatInfo(TestFormatBase):

    def test__format_info_constructor(self):
        def validate(ft, system, fmt, expected):
            self.assertEqual(ft.system, system)
            self.assertEqual(ft.fmt, fmt)
            self.assertEqual(ft.domain, expected["domain"])
            self.assertEqual(ft.options, expected["options"])
            self.assertEqual(ft.info, expected["info"])
            self.assertEqual(ft.alt_fmt, expected["alt_fmt"])

        inputs = {
            "{a.b}": {
                "system": self.system_mock,
                "domain": "a",
                "options": None,
                "info": "b",
                "alt_fmt": None
            },
            "{a.b[c]}": {
                "system": self.system_mock,
                "domain": "a",
                "options": "c",
                "info": "b",
                "alt_fmt": None
            },
            "{a.b[c]?d}": {
                "system": self.system_mock,
                "domain": "a",
                "options": "c",
                "info": "b",
                "alt_fmt": "d"
            }
        }

        for key, value in inputs.items():
            ft = FormatInfo(value["system"], key)
            validate(ft, value["system"], key, value)

    def test__format_info_build_simple(self):
        self.test_mock_a.query.return_value = "testing"
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b}")

        self.assertEqual(ft.build(), "testing")

        args_system, _ = self.system_mock.query.call_args
        args_a, _ = self.test_mock_a.query.call_args

        self.assertEqual(args_system, ("a",))
        self.assertEqual(args_a, ("b", None))

    def test__format_info_build_invalid(self):
        self.test_mock_a.query.return_value = False
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b}")
        self.assertEqual(ft.build(), "")
        self.test_mock_a.query.return_value = None
        ft = FormatInfo(self.system_mock, "{a.b}")
        self.assertEqual(ft.build(), "")

    def test__format_info_build_alternate(self):
        self.test_mock_a.query.return_value = "valid"
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b?this is valid}")
        self.assertEqual(ft.build(), "this is valid")

    def test__format_info_build_alternate_ignore(self):
        self.test_mock_a.query.return_value = False
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b?this should not appear}")
        self.assertEqual(ft.build(), "")

    def test__format_info_build_alternate_with_info(self):
        self.test_mock_a.query.return_value = "valid"
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b?this is also valid: {}}")
        self.assertEqual(ft.build(), "this is also valid: valid")

    def test__format_info_build_alternate_with_info_and_other_info(self):
        self.test_mock_a.query.return_value = "a_valid"
        self.test_mock_c.query.return_value = "c_valid"
        self.system_mock.query.side_effect = [self.test_mock_a,
                                              self.test_mock_c]
        ft = FormatInfo(self.system_mock, "{a.b?{} {c.d}}")

        self.assertEqual(ft.build(), "a_valid c_valid")

        args_a, _ = self.test_mock_a.query.call_args
        args_c, _ = self.test_mock_c.query.call_args

        self.assertEqual(args_a, ("b", None))
        self.assertEqual(args_c, ("d", None))

    def test__format_info_build_with_options(self):
        self.test_mock_a.query.return_value = "options"
        self.system_mock.query.return_value = self.test_mock_a
        ft = FormatInfo(self.system_mock, "{a.b[c]}")

        self.assertEqual(ft.build(), "options")
        args, _ = self.test_mock_a.query.call_args
        self.assertEqual(args, ("b", "c"))
