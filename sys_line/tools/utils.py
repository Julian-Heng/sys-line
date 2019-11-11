#!/usr/bin/env python3
# pylint: disable=pointless-string-statement,cyclic-import,invalid-name

""" Utility module to provide common functions """

import os
import re
import subprocess
import sys
import typing

from pathlib import Path

from .storage import Storage


def percent(num_1: typing.Union[int, float, Storage],
            num_2: typing.Union[int, float, Storage]) -> (
                typing.Union[float, Storage]):
    """ Returns percent of 2 numbers """
    return (num_1 / num_2) * 100 if num_2 else None


def open_read(filename: typing.Union[Path, str]) -> typing.List[str]:
    """
    Wrapper for opening and reading a file

    Pathlib for python <= 3.5 can't open properly when passed to open(). So an
    edge case is required to convert the pathlib object to string
    """
    with open(str(filename) if sys.version_info[1] <= 5 else filename) as f:
        return f.read()


def run(cmd: typing.List[str]) -> str:
    """ Runs cmd and returns output as a string """
    stdout = subprocess.PIPE
    stderr = open(os.devnull, "w")
    process = subprocess.run(cmd, stdout=stdout, stderr=stderr)
    return process.stdout.decode("utf-8")


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

    _str = re.sub(r"\s+", " ", string.strip())
    return _str if _str else None


def _round(num: float, rnd: int) -> typing.Union[int, float]:
    """ Wrapper for round method to trim whole float numbers """
    ret = round(num, rnd)
    return int(ret) if rnd == 0 or ret == int(num) else ret
