#!/usr/bin/env python3

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
        inputs = [
            {},
            {"a": "b"},
            {"a": {"b": "c"}},
            {"x": {"a": {"b": "c"}, "d": ["e", "f"]}, "y": ("z")},
        ]

        for i in inputs:
            self._validate(dict_to_namespace(i), i)

    def _validate(self, nspace, attr_dict):
        self.assertEqual(isinstance(nspace, SimpleNamespace), True)
        for key in attr_dict.keys():
            self.assertEqual(hasattr(nspace, key), True)
            value = getattr(nspace, key)
            if isinstance(value, SimpleNamespace):
                self._validate(value, attr_dict[key])
            else:
                self.assertEqual(value, attr_dict[key])
