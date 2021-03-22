#!/usr/bin/env python3

from datetime import datetime

from sys_line.core.plugin.abstract import AbstractPlugin


class Date(AbstractPlugin):
    """ Date class to fetch date and time """

    @staticmethod
    def _format(fmt):
        """ Wrapper for printing date and time format """
        return "{{:{}}}".format(fmt).format(datetime.now())

    def date(self, options=None):
        """ Returns the date as a string from a specified format """
        if options is None:
            options = self.default_options

        return Date._format(options.date.format)

    def time(self, options=None):
        """ Returns the time as a string from a specified format """
        if options is None:
            options = self.default_options

        return Date._format(options.time.format)
