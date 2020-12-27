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

# pylint: disable=pointless-string-statement,cyclic-import,invalid-name

""" Utility module to provide common functions """

import os
import re
import subprocess
import sys


def percent(num_1, num_2):
    """ Returns percent of 2 numbers """
    return (num_1 / num_2) * 100 if num_2 else None


def open_read(filename):
    """
    Wrapper for opening and reading a file
    """
    # Pathlib for python <= 3.5 can't open properly when passed to open(). So
    # an edge case is required to convert the pathlib object to string
    if sys.version_info[1] <= 5:
        filename = str(filename)

    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


def run(cmd):
    """ Runs cmd and returns output as a string """
    with open(os.devnull, "w") as stderr:
        stdout = subprocess.PIPE
        process = subprocess.run(cmd, stdout=stdout, stderr=stderr,
                                 check=False)
        return process.stdout.decode("utf-8")


def unix_epoch_to_str(secs):
    """ Convert unix time to human readable output """
    days = int(secs / 86400)
    hours = int((secs / 3600) % 24)
    mins = int((secs / 60) % 60)
    secs = (secs % 60) % 60

    days = f"{days}d" if days else ""
    hours = f"{hours}h" if hours else ""
    mins = f"{mins}m" if mins else ""
    secs = f"{secs}s" if secs else ""

    string = f"{days} {hours} {mins} {secs}"
    string = trim_string(string)
    return string if string else None


def round_trim(num, rnd):
    """ Wrapper for round method to trim whole float numbers """
    ret = round(num, rnd)
    return int(ret) if rnd == 0 or ret == int(num) else ret


def trim_string(string):
    """ Trims the string of whitespaces """
    return re.sub(r"\s+", " ", string.strip())
