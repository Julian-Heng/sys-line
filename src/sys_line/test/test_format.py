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
        self.system_valid = MagicMock(spec=System)


class TestFormatTree(TestFormatBase):

    def test__format_tree_contructor(self):
        ft = FormatTree(self.system_valid, "")
        self.assertEqual(ft.system, self.system_valid)
        self.assertEqual(ft.fmt, "")
        self.assertEqual(ft.tokens, [])

        string = "this is a string"
        ft = FormatTree(self.system_valid, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, [string])

        string = "this has info {a.b}"
        ft = FormatTree(self.system_valid, string)
        self.assertEqual(ft.fmt, string)
        self.assertEqual(ft.tokens, ["this has info ", "{a.b}"])


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
                "system": self.system_valid,
                "domain": "a",
                "options": None,
                "info": "b",
                "alt_fmt": None
            },
            "{a[c].b}": {
                "system": self.system_valid,
                "domain": "a",
                "options": "c",
                "info": "b",
                "alt_fmt": None
            },
            "{a[c].b?d}": {
                "system": self.system_valid,
                "domain": "a",
                "options": "c",
                "info": "b",
                "alt_fmt": "d"
            }
        }

        for key, value in inputs.items():
            ft = FormatInfo(value["system"], key)
            validate(ft, value["system"], key, value)
