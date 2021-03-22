#!/usr/bin/env python3

from pathlib import Path
from logging import getLogger

from sys_line.core.plugin.net.abstract import AbstractNetwork
from sys_line.tools.utils import open_read


LOG = getLogger(__name__)


class Network(AbstractNetwork):
    """ A Linux implementation of the AbstractNetwork class """

    _FILES = {
        "sys_net": Path("/sys/class/net"),
        "proc_wifi": Path("/proc/net/wireless"),
    }

    @property
    def _LOCAL_IP_CMD(self):
        return ["ip", "address", "show", "dev"]

    def dev(self, options=None):
        def check(_file):
            _file = _file.joinpath("operstate")
            _file_contents = open_read(_file)
            if _file_contents is None:
                return False
            return "up" in _file_contents

        # Skip virtual network devices
        files = Network._FILES["sys_net"].glob("[!v]*")
        dev_dir = next(filter(check, files), None)
        if dev_dir is None:
            return None
        return dev_dir.name

    def _ssid(self):
        dev = self.dev()
        if dev is None:
            LOG.debug("unable to get network device")
            return None, None

        wifi_path = Network._FILES["proc_wifi"]
        wifi_out = open_read(wifi_path)
        if not wifi_out:
            LOG.debug("unable to read proc wireless file '%s'", wifi_path)
            return None, None

        wifi_out = wifi_out.strip().splitlines()
        if len(wifi_out) < 3:
            LOG.debug(
                "proc wireless file does not contain any wireless connections"
            )
            return None, None

        iw_exe = which("iw")
        if not iw_exe:
            LOG.debug("unable to find iw binary")
            return None, None

        ssid_cmd = (iw_exe, "dev", dev, "link")
        ssid_reg = re.compile(r"^SSID: (.*)$")
        return ssid_cmd, ssid_reg

    def _bytes_delta(self, dev, mode):
        net = Network._FILES["sys_net"]
        if mode == "up":
            mode = "tx"
        else:
            mode = "rx"

        stat_file = Path(net, dev, "statistics", f"{mode}_bytes")
        stat = open_read(stat_file)
        if stat is None:
            return None

        stat = int(stat)
        return stat


