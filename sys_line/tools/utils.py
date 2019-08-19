#!/usr/bin/env python3
# pylint: disable=pointless-string-statement

""" Utility module to provide common functions """

import os
import re
import subprocess
import sys

from typing import List

from .storage import Storage


def percent(num_1: [int, float, Storage],
            num_2: [int, float, Storage]) -> [float, Storage]:
    """ Returns percent of 2 numbers """
    return (num_1 / num_2) * 100 if num_2 else None


"""
Pathlib for python <= 3.5 can't open properly when passed to open(). So an edge
case is required to convert the pathlib object to string
"""
if sys.version_info[1] <= 5:
    def open_read(filename: str) -> List[str]:
        """ Wrapper for opening and reading a file """
        with open(str(filename)) as _file:
            contents = _file.read()
        return contents
else:
    def open_read(filename: str) -> List[str]:
        """ Wrapper for opening and reading a file """
        with open(filename) as _file:
            contents = _file.read()
        return contents


def run(cmd: List[str]) -> str:
    """ Runs cmd and returns output as a string """
    stdout = subprocess.PIPE
    stderr = open(os.devnull, "w")
    return (subprocess.run(cmd, stdout=stdout, stderr=stderr)
            .stdout.decode("utf-8"))


def unix_epoch_to_str(secs: int) -> str:
    """ Convert unix time to human readable output """
    days = int(secs / 86400)
    hours = int((secs / 3600) % 24)
    mins = int((secs / 60) % 60)
    secs = (secs % 60) % 60
    string = "{} {} {} {}".format(
        "{}d".format(days) if days else "",
        "{}h".format(hours) if hours else "",
        "{}m".format(mins) if mins else "",
        "{}s".format(secs) if secs else ""
    )

    return re.sub(r"\s+", " ", string.strip())


def _round(num: float, rnd: int) -> [int, float]:
    """ Wrapper for round method to trim whole float numbers """
    ret = round(num, rnd)
    return int(ret) if rnd == 0 or ret == int(num) else ret
