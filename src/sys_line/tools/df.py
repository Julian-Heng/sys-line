#!/usr/bin/env python3
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
