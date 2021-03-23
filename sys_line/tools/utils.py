#!/usr/bin/env python3

# sys-line - a simple status line generator
# Copyright (C) 2019-2021  Julian Heng
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

import itertools
import os
import re
import shutil
import subprocess

from functools import lru_cache
from logging import getLogger
from types import SimpleNamespace


LOG = getLogger(__name__)


def percent(num_1, num_2):
    """ Returns percent of 2 numbers """
    return (num_1 / num_2) * 100 if num_2 else None


def open_read(filename):
    """ Wrapper for opening and reading a file """
    LOG.debug("opening file '%s'", filename)
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        LOG.debug("file '%s' does not exist", filename)
        return None


def run(cmd):
    """ Runs cmd and returns output as a string """
    LOG.debug("running command: %s", cmd)
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


def namespace_types_as_dict(o):
    """
    Returns a dictionary in the same structure as the given namespace except
    with types as values
    """
    if isinstance(o, SimpleNamespace):
        return {k: namespace_types_as_dict(v) for k, v in o.__dict__.items()}
    return type(o)


@lru_cache()
def which(exe_name):
    """ Returns the absolute path to the executable """
    return shutil.which(exe_name)


@lru_cache(maxsize=1)
def linux_mem_file():
    """ Returns a cached dictionary of /proc/meminfo """
    reg = re.compile(r"\s+|kB")
    mem_file = open_read("/proc/meminfo")
    if mem_file is None:
        LOG.debug("unable to read memory info file '%s'", mem_file)
        return dict()

    mem_file = mem_file.strip().splitlines()
    mem_file = dict(reg.sub("", i).split(":", 1) for i in mem_file)
    mem_file = {k: int(v) for k, v in mem_file.items()}
    return mem_file


def flatten(_list):
    """ Converts a list of lists into a single list """
    return list(itertools.chain(*_list))


def unique(_list):
    """ Removes duplicate values in a list """
    return list(dict.fromkeys(_list))
