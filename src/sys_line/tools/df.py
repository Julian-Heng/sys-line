#!/usr/bin/env python3

""" df model class """


class DfEntry():

    def __init__(self, filesystem, blocks, used, available, percent, mount):
        self._filesystem = filesystem
        self._blocks = blocks
        self._used = used
        self._available = available
        self._percent = percent
        self._mount = mount

    @property
    def filesystem(self):
        return self._filesystem

    @property
    def blocks(self):
        return self._blocks

    @property
    def used(self):
        return self._used

    @property
    def available(self):
        return self._available

    @property
    def percent(self):
        return self._percent

    @property
    def mount(self):
        return self._mount
