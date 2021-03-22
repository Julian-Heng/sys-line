#!/usr/bin/env python3

import re

from pathlib import Path
from functools import lru_cache

from sys_line.core.plugin.misc.abstract import AbstractMisc
from sys_line.tools.utils import open_read, percent, run, which


class Misc(AbstractMisc):
    """ A Linux implementation of the AbstractMisc class """

    _FILES = {
        "proc": Path("/proc"),
        "sys_backlight": Path("/sys/devices/backlight"),
    }

    def _vol(self):
        systems = {"pulseaudio": Misc._vol_pulseaudio}
        reg = re.compile(r"|".join(systems.keys()))

        proc = Misc._FILES["proc"]
        pids = (open_read(d.joinpath("cmdline")) for d in proc.iterdir()
                if d.is_dir() and d.name.isdigit())
        audio = (reg.search(i) for i in pids if i and reg.search(i))
        audio = next(audio, None)

        if audio is None:
            return None

        try:
            vol = systems[audio.group(0)]()
        except KeyError:
            vol = None

        return vol

    def _scr(self):
        def check(_file):
            _filename = _file.name
            return "kbd" not in _filename and "backlight" not in _filename

        backlight_path = Misc._FILES["sys_backlight"]
        if not backlight_path.exists():
            return None, None

        backlight_glob = backlight_path.rglob("*")
        scr_dir = next(filter(check, backlight_glob), None)
        if scr_dir is None:
            LOG.debug("unable to find backlight directory")
            return None, None

        current_scr = open_read(scr_dir.joinpath("brightness"))
        max_scr = open_read(scr_dir.joinpath("max_brightness"))

        if current_scr is None or max_scr is None:
            if current_scr is None:
                LOG.debug("unable to read current screen brightness file '%s'",
                          current_scr)
            if max_scr is None:
                LOG.debug("unable to read max screen brightness file '%s'",
                          max_scr)
            return None, None

        current_scr = current_scr.strip()
        max_scr = max_scr.strip()

        if not current_scr.isnumeric() or not max_scr.isnumeric():
            if not current_scr.isnumeric():
                LOG.debug("unable to read current screen brightness file '%s'",
                          current_scr)
            if not max_scr.isnumeric():
                LOG.debug("unable to read max screen brightness file '%s'",
                          max_scr)
            return None, None

        return current_scr, max_scr

    @staticmethod
    @lru_cache(maxsize=1)
    def _vol_pulseaudio():
        """ Return system volume using pulse audio """
        default_reg = re.compile(r"^set-default-sink (.*)$", re.M)
        pacmd_exe = which("pacmd")
        if not pacmd_exe:
            LOG.debug("unable to find pacmd binary")
            return None

        pac_dump = run([pacmd_exe, "dump"])
        if pac_dump is None:
            LOG.debug("unable to get output from pacmd")
            return None

        default = default_reg.search(pac_dump)
        if default is None:
            LOG.debug("unable to process output from pacmd")
            return None

        vol_reg = fr"^set-sink-volume {default.group(1)} 0x(.*)$"
        vol_reg = re.compile(vol_reg, re.M)
        vol = vol_reg.search(pac_dump)

        if vol is None:
            return None

        vol = vol.group(1)
        vol = int(vol, 16)
        vol = percent(vol, 0x10000)
        return vol
