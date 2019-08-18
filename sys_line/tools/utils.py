#!/usr/bin/env python3

""" Utility module to provide common functions """

import os
import re
import subprocess
import sys


def percent(num_1, num_2):
    """ Calculate percentage """
    return None if num_2 == 0 else (num_1 / num_2) * 100


"""
Pathlib for python <= 3.5 can't open properly when passed to open(). So an edge
case is required to convert the pathlib object to string
"""
if sys.version_info[1] <= 5:
    def open_read(filename):
        """ Wrapper for opening and reading a file """
        with open(str(filename)) as _file:
            contents = _file.read()
        return contents
else:
    def open_read(filename):
        """ Wrapper for opening and reading a file """
        with open(filename) as _file:
            contents = _file.read()
        return contents


def run(cmd):
    """ Runs cmd and returns output as a string """
    stdout = subprocess.PIPE
    stderr = open(os.devnull, "w")
    return (subprocess.run(cmd, stdout=stdout, stderr=stderr)
            .stdout.decode("utf-8"))


def unix_epoch_to_str(secs):
    """ Convert unix time to human readable output """
    days = int(secs / 60 / 60 / 24)
    hours = int(secs / 60 / 60 % 24)
    mins = int(secs / 60 % 60)
    secs = (secs % 60) % 60
    string = "{} {} {} {}s".format(
        "{}d".format(days) if days != 0 else "",
        "{}h".format(hours) if hours != 0 else "",
        "{}m".format(mins) if mins != 0 else "",
        secs)

    string = re.sub(r"\s+", " ", string.strip())
    return string


def _round(num, rnd):
    """ Wrapper for round method to trim whole float numbers """
    ret = round(num, rnd)
    return int(ret) if rnd == 0 or ret == int(num) else ret
