#!/usr/bin/env python3

import unittest

from ..tools.storage import Storage as Storage


class TestStorage(unittest.TestCase):

    def test__storage_constructor(self):
        stor = Storage(0, "B")
        self.assertEqual(stor.value, 0)
        self.assertEqual(stor.prefix, "B")
        self.assertEqual(stor.rounding, -1)
        self.assertEqual(stor._bytes, None)

        stor = Storage(1024, "B")
        self.assertEqual(stor.value, 1024)
        self.assertEqual(stor.prefix, "B")
        self.assertEqual(stor.rounding, -1)
        self.assertEqual(stor._bytes, None)

        stor = Storage(1024, "B", rounding=3)
        self.assertEqual(stor.value, 1024)
        self.assertEqual(stor.prefix, "B")
        self.assertEqual(stor.rounding, 3)
        self.assertEqual(stor._bytes, None)

    def test__storage_bytes(self):
        stor = Storage(1, "B")
        self.assertEqual(stor.bytes, 1)

        stor = Storage(1, "KiB")
        self.assertEqual(stor.bytes, 1024)

        stor = Storage(1, "MiB")
        self.assertEqual(stor.bytes, 1024 * 1024)

        stor = Storage(1, "GiB")
        self.assertEqual(stor.bytes, 1024 * 1024 * 1024)

    def test__storage_prefix(self):
        stor = Storage(1024, "KiB")
        stor.prefix = "MiB"
        self.assertEqual(stor.value, 1)

        stor = Storage(1024 * 1024, "KiB")
        stor.prefix = "GiB"
        self.assertEqual(stor.value, 1)

        stor = Storage(1, "GiB")
        stor.prefix = "MiB"
        self.assertEqual(stor.value, 1024)

        stor = Storage(1, "GiB")
        stor.prefix = "KiB"
        self.assertEqual(stor.value, 1024 * 1024)

    def test__storage_string(self):
        self.assertEqual(str(Storage(1, "B")), "1 B")
        self.assertEqual(str(Storage(1, "KiB")), "1 KiB")
        self.assertEqual(str(Storage(1.511, "KiB", rounding=2)), "1.51 KiB")
