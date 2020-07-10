#!/usr/bin/env python3

import unittest

from unittest.mock import MagicMock

from ..tools.format import FormatTree, FormatInfo, Tokenizer
from ..systems.abstract import System


class TestTokenizer(unittest.TestCase):

    def test__tokenizer(self):
        inputs = [
            ("", []),
            ("a", ["a"]),
            ("a b", ["a b"]),
            ("a {a.b}", ["a ", "{a.b}"]),
            ("a {a.b?{c.d}}", ["a ", "{a.b?{c.d}}"]),
            ("a {a[z].b?{c.d}}", ["a ", "{a[z].b?{c.d}}"]),
            ("a {a.b} {c.d}", ["a ", "{a.b}", " ", "{c.d}"])
        ]

        for i in inputs:
            string, expected = i
            self.assertEqual(Tokenizer.tokenize(string), expected)


class TestFormatBase(unittest.TestCase):

    def setUp(self):
        self.system_mock = MagicMock()


class TestFormatTree(TestFormatBase):

    def test__format_tree_contructor(self):
        ft = FormatTree(self.system_mock, "")
        self.assertEqual(ft.system, self.system_mock)
        self.assertEqual(ft.fmt, "")
        self.assertEqual(ft.tokens, [])

        string = "this is a string"
        ft = FormatTree(self.system_mock, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, [string])

        string = "this has info {a.b}"
        ft = FormatTree(self.system_mock, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, ["this has info ", "{a.b}"])

    def test__format_tree_build(self):
        self.system_mock.a.query.return_value = "a_b"
        ft = FormatTree(self.system_mock, "| {a.b} |")
        self.assertEqual(ft.build(), "| a_b |")

        self.system_mock.a.query.return_value = False
        ft = FormatTree(self.system_mock, "| {a.b} |")
        self.assertEqual(ft.build(), "|  |")

        self.system_mock.a.query.return_value = False
        ft = FormatTree(self.system_mock, "| {a.b?sub} |")
        self.assertEqual(ft.build(), "|  |")

        self.system_mock.a.query.return_value = True
        ft = FormatTree(self.system_mock, "| {a.b?sub} |")
        self.assertEqual(ft.build(), "| sub |")

        self.system_mock.a.query.return_value = "a_b"
        self.system_mock.c.query.return_value = "c_d"
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
            "{a[c].b}": {
                "system": self.system_mock,
                "domain": "a",
                "options": "c",
                "info": "b",
                "alt_fmt": None
            },
            "{a[c].b?d}": {
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

    def test__format_info_build(self):
        self.system_mock.a.query.return_value = "testing"
        ft = FormatInfo(self.system_mock, "{a.b}")
        self.assertEqual(ft.build(), "testing")
        self.assertEqual(self.system_mock.a.query.call_args.args, ("b", None))

        self.system_mock.a.query.return_value = False
        ft = FormatInfo(self.system_mock, "{a.b}")
        self.assertEqual(ft.build(), "")

        self.system_mock.a.query.return_value = False
        ft = FormatInfo(self.system_mock, "{a.b?this should not appear}")
        self.assertEqual(ft.build(), "")

        self.system_mock.a.query.return_value = "valid"
        ft = FormatInfo(self.system_mock, "{a.b?this is valid}")
        self.assertEqual(ft.build(), "this is valid")

        self.system_mock.a.query.return_value = "valid"
        ft = FormatInfo(self.system_mock, "{a.b?this is also valid: {}}")
        self.assertEqual(ft.build(), "this is also valid: valid")

        self.system_mock.a.query.return_value = "a_valid"
        self.system_mock.c.query.return_value = "c_valid"
        ft = FormatInfo(self.system_mock, "{a.b?{} {c.d}}")
        self.assertEqual(ft.build(), "a_valid c_valid")
        self.assertEqual(self.system_mock.a.query.call_args.args, ("b", None))
        self.assertEqual(self.system_mock.c.query.call_args.args, ("d", None))

        self.system_mock.a.query.return_value = "options"
        ft = FormatInfo(self.system_mock, "{a[c].b}")
        self.assertEqual(ft.build(), "options")
        self.assertEqual(self.system_mock.a.query.call_args.args, ("b", "c"))
