#!/usr/bin/env python3
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

    Pathlib for python <= 3.5 can't open properly when passed to open(). So an
    edge case is required to convert the pathlib object to string
    """
    with open(str(filename) if sys.version_info[1] <= 5 else filename) as f:
        return f.read()


def run(cmd):
    """ Runs cmd and returns output as a string """
    stdout = subprocess.PIPE
    stderr = open(os.devnull, "w")
    process = subprocess.run(cmd, stdout=stdout, stderr=stderr, check=False)
    return process.stdout.decode("utf-8")


def unix_epoch_to_str(secs):
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

    string = trim_string(string)
    return string if string else None


def round_trim(num, rnd):
    """ Wrapper for round method to trim whole float numbers """
    ret = round(num, rnd)
    return int(ret) if rnd == 0 or ret == int(num) else ret


def trim_string(string):
    """ Trims the string of whitespaces """
    return re.sub(r"\s+", " ", string.strip())
