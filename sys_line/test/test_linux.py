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

# TODO:
#   - Battery tests
#   - Misc tests

import unittest

from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

from ..systems.linux import Linux, _mem_file
from ..tools.cli import parse_cli
from ..tools.utils import which


class TestLinux(unittest.TestCase):

    def setUp(self):
        super(TestLinux, self).setUp()
        self.system = Linux(parse_cli([]))
        self.run_patch = patch("sys_line.systems.linux.run").start()
        which.cache_clear()

    def tearDown(self):
        super(TestLinux, self).tearDown()
        patch.stopall()

    @staticmethod
    def get_open_patch(read_data=""):
        return patch("sys_line.tools.utils.open", new_callable=mock_open,
                     read_data=read_data, create=True)

    @staticmethod
    def get_open_patch_multiple(read_datas=tuple()):
        try:
            _iter = iter(read_datas)
            first = next(_iter)
        except (TypeError, StopIteration):
            return TestLinux.get_open_patch(read_data=None)

        m = mock_open(read_data=first)
        m.side_effect = (
            mock_open(read_data=d).return_value for d in read_datas
        )
        return patch("sys_line.tools.utils.open", m, create=True)


class TestLinuxCpu(TestLinux):

    CPU_FILE= """processor       : 0
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz
stepping        : 3
microcode       : 0x28
cpu MHz         : 3448.812
cache size      : 6144 KB
physical id     : 0
siblings        : 4
core id         : 0
cpu cores       : 4
apicid          : 0
initial apicid  : 0
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts md_clear flush_l1d
vmx flags       : vnmi preemption_timer invvpid ept_x_only ept_ad ept_1gb flexpriority tsc_offset vtpr mtf vapic ept vpid unrestricted_guest ple shadow_vmcs
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit srbds
bogomips        : 6599.62
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

processor       : 1
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz
stepping        : 3
microcode       : 0x28
cpu MHz         : 3394.770
cache size      : 6144 KB
physical id     : 0
siblings        : 4
core id         : 1
cpu cores       : 4
apicid          : 2
initial apicid  : 2
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts md_clear flush_l1d
vmx flags       : vnmi preemption_timer invvpid ept_x_only ept_ad ept_1gb flexpriority tsc_offset vtpr mtf vapic ept vpid unrestricted_guest ple shadow_vmcs
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit srbds
bogomips        : 6599.62
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

processor       : 2
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz
stepping        : 3
microcode       : 0x28
cpu MHz         : 3423.144
cache size      : 6144 KB
physical id     : 0
siblings        : 4
core id         : 2
cpu cores       : 4
apicid          : 4
initial apicid  : 4
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts md_clear flush_l1d
vmx flags       : vnmi preemption_timer invvpid ept_x_only ept_ad ept_1gb flexpriority tsc_offset vtpr mtf vapic ept vpid unrestricted_guest ple shadow_vmcs
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit srbds
bogomips        : 6599.62
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

processor       : 3
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz
stepping        : 3
microcode       : 0x28
cpu MHz         : 3403.148
cache size      : 6144 KB
physical id     : 0
siblings        : 4
core id         : 3
cpu cores       : 4
apicid          : 6
initial apicid  : 6
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts md_clear flush_l1d
vmx flags       : vnmi preemption_timer invvpid ept_x_only ept_ad ept_1gb flexpriority tsc_offset vtpr mtf vapic ept vpid unrestricted_guest ple shadow_vmcs
bugs            : cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit srbds
bogomips        : 6599.62
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:
"""

    SPEED_FILE = "3700000\n"
    LOAD_FILE = "1.06 1.09 1.15 2/996 281756\n"
    FAN_FILE = "1234\n"
    TEMP_FILE = "58000\n"
    UPTIME_FILE = "45516.13 123925.62\n"

    def setUp(self):
        super(TestLinuxCpu, self).setUp()
        self.cpu = self.system.query("cpu")

        self.cpu_speed_file_path_patch = (
            patch("sys_line.systems.linux.Cpu._cpu_speed_file_path",
                  new_callable=PropertyMock).start()
        )

        self.cpu_temp_file_paths_patch = (
            patch("sys_line.systems.linux.Cpu._cpu_temp_file_paths",
                  new_callable=PropertyMock).start()
        )

        self.cpu_fan_file_path_patch = (
            patch("sys_line.systems.linux.Cpu._cpu_fan_file_path",
                  new_callable=PropertyMock).start()
        )

    @TestLinux.get_open_patch(read_data=CPU_FILE)
    def test__linux_cpu_cores(self, mock_file):
        self.assertEqual(self.cpu.query("cores", None), 4)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/cpuinfo"), "r"))

    @TestLinux.get_open_patch(read_data=CPU_FILE)
    def test__linux_cpu_string(self, mock_file):
        expected = "Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz"
        self.assertEqual(self.cpu._cpu_string(), expected)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/cpuinfo"), "r"))

    @TestLinux.get_open_patch(read_data=SPEED_FILE)
    def test__linux_cpu_speed_valid(self, mock_file):
        self.cpu_speed_file_path_patch.return_value = "stub"
        self.assertEqual(self.cpu._cpu_speed(), 3.7)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, ("stub", "r"))

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_cpu_speed_invalid(self, mock_file):
        self.cpu_speed_file_path_patch.return_value = None
        self.assertEqual(self.cpu._cpu_speed(), None)
        self.assertFalse(mock_file.called)

    @TestLinux.get_open_patch(read_data=LOAD_FILE)
    def test__linux_cpu_load_avg_valid(self, mock_file):
        expected = ["1.06", "1.09", "1.15"]
        self.assertEqual(self.cpu._load_avg(), expected)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/loadavg"), "r"))

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_cpu_load_avg_invalid(self, mock_file):
        mock_file.side_effect = FileNotFoundError
        self.assertEqual(self.cpu._load_avg(), None)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/loadavg"), "r"))

    @TestLinux.get_open_patch(read_data=FAN_FILE)
    def test__linux_cpu_fan_valid(self, mock_file):
        self.cpu_fan_file_path_patch.return_value = "stub"
        self.assertEqual(self.cpu.fan(), 1234)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, ("stub", "r"))

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_cpu_fan_invalid(self, mock_file):
        self.cpu_fan_file_path_patch.return_value = None
        self.assertEqual(self.cpu.fan(), None)
        self.assertFalse(mock_file.called)

    @TestLinux.get_open_patch(read_data=TEMP_FILE)
    def test__linux_cpu_temp_valid(self, mock_file):
        self.cpu_temp_file_paths_patch.return_value = ["stub1", "stub2"]
        self.assertEqual(self.cpu.temp(), 58.0)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, ("stub1", "r"))

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_cpu_temp_invalid(self, mock_file):
        self.cpu_temp_file_paths_patch.return_value = None
        self.assertEqual(self.cpu.temp(), None)
        self.assertFalse(mock_file.called)

    @TestLinux.get_open_patch(read_data=UPTIME_FILE)
    def test__linux_cpu_uptime_valid(self, mock_file):
        self.assertEqual(self.cpu._uptime(), 45516)
        args, _ = mock_file.call_args
        self.assertTrue(mock_file.called)
        self.assertEqual(args, (Path("/proc/uptime"), "r"))

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_cpu_uptime_invalid(self, mock_file):
        mock_file.side_effect = FileNotFoundError
        self.assertEqual(self.cpu._uptime(), None)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/uptime"), "r"))


class _TestLinuxMemFile(TestLinux):

    MEM_FILE = """MemTotal:       16260004 kB
MemFree:         8172964 kB
MemAvailable:   12541728 kB
Buffers:          576268 kB
Cached:          4798564 kB
SwapCached:            0 kB
Active:          1748660 kB
Inactive:        5302088 kB
Active(anon):      24976 kB
Inactive(anon):  2505580 kB
Active(file):    1723684 kB
Inactive(file):  2796508 kB
Unevictable:      614112 kB
Mlocked:              32 kB
SwapTotal:             0 kB
SwapFree:              0 kB
Dirty:              5432 kB
Writeback:             0 kB
AnonPages:       2289976 kB
Mapped:           823120 kB
Shmem:            865948 kB
KReclaimable:     185588 kB
Slab:             258232 kB
SReclaimable:     185588 kB
SUnreclaim:        72644 kB
KernelStack:       13104 kB
PageTables:        25884 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:     8130000 kB
Committed_AS:    8528624 kB
VmallocTotal:   34359738367 kB
VmallocUsed:       31976 kB
VmallocChunk:          0 kB
Percpu:             2240 kB
HardwareCorrupted:     0 kB
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
ShmemPmdMapped:        0 kB
FileHugePages:         0 kB
FilePmdMapped:         0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
DirectMap4k:      326580 kB
DirectMap2M:    15267840 kB
DirectMap1G:     1048576 kB
"""


class TestLinuxMem(_TestLinuxMemFile):

    def setUp(self):
        super(TestLinuxMem, self).setUp()
        self.mem = self.system.query("mem")

    @TestLinux.get_open_patch(read_data=_TestLinuxMemFile.MEM_FILE)
    def test__linux_mem_file(self, mock_file):
        mem_file = _mem_file()
        keys = ("MemTotal", "Shmem", "MemFree", "Buffers", "Cached",
                "SReclaimable", "MemTotal")
        self.assertTrue(all(k in mem_file.keys() for k in keys))
        args, _ = mock_file.call_args
        self.assertEqual(args, ("/proc/meminfo", "r"))

    def test__linux_mem_used(self):
        self.assertEqual(self.mem._used(), (3392568, "KiB"))

    def test__linux_mem_total(self):
        self.assertEqual(self.mem._total(), (16260004, "KiB"))


class TestLinuxSwap(TestLinux):

    def setUp(self):
        super(TestLinuxSwap, self).setUp()
        self.swap = self.system.query("swap")

    def test__linux_swap_used(self):
        self.assertEqual(self.swap._used(), (0, "KiB"))

    def test__linux_swap_total(self):
        self.assertEqual(self.swap._total(), (0, "KiB"))


class TestLinuxDisk(TestLinux):

    def setUp(self):
        super(TestLinuxDisk, self).setUp()

        self.disk = self.system.query("disk")

        self.original_dev_mock_single = {
            "/dev/sdb4": "/dev/sdb4",
        }

        self.original_dev_mock_multiple = {
            "/dev/sdb4": "/dev/sdb4",
            "/dev/sdb5": "/dev/sdb5",
        }

        # Output of
        # 'lsblk --output NAME,LABEL,PARTLABEL,FSTYPE --paths --pairs'
        self.lsblk_out = """NAME="/dev/sdb4" LABEL="" PARTLABEL="root" FSTYPE="ext4"
NAME="/dev/sdb2" LABEL="" PARTLABEL="boot" FSTYPE="ext4"
NAME="/dev/sdb5" LABEL="" PARTLABEL="home" FSTYPE="ext4"
NAME="/dev/sdb3" LABEL="" PARTLABEL="efi" FSTYPE="vfat"
NAME="/dev/sdb1" LABEL="" PARTLABEL="bios_grub" FSTYPE=""
"""

        self.which_patch = patch("shutil.which").start()
        self.which_patch.return_value = True

        self.dev_patch = (
            patch("sys_line.systems.linux.Disk._original_dev").start()
        )

        self.run_patch.return_value = self.lsblk_out

    def test__linux_lsblk_not_installed(self):
        self.which_patch.return_value = False
        entries = self.disk._lsblk_entries
        self.assertEqual(entries, None)

    def test__linux_lsblk_entries(self):
        entries = self.disk._lsblk_entries
        expected = {
            "/dev/sdb4": {
                "NAME": "/dev/sdb4",
                "LABEL": "",
                "PARTLABEL": "root",
                "FSTYPE": "ext4",
            },
            "/dev/sdb2": {
                "NAME": "/dev/sdb2",
                "LABEL": "",
                "PARTLABEL": "boot",
                "FSTYPE": "ext4",
            },
            "/dev/sdb5": {
                "NAME": "/dev/sdb5",
                "LABEL": "",
                "PARTLABEL": "home",
                "FSTYPE": "ext4",
            },
            "/dev/sdb3": {
                "NAME": "/dev/sdb3",
                "LABEL": "",
                "PARTLABEL": "efi",
                "FSTYPE": "vfat",
            },
            "/dev/sdb1": {
                "NAME": "/dev/sdb1",
                "LABEL": "",
                "PARTLABEL": "bios_grub",
                "FSTYPE": "",
            },
        }

        self.assertEqual(entries, expected)


class TestLinuxDiskSingle(TestLinuxDisk):

    def setUp(self):
        super(TestLinuxDiskSingle, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_single
        self.run_patch.return_value = self.lsblk_out

    def test__linux_disk_lsblk_not_installed_single(self):
        self.which_patch.return_value = False

        expected = {"/dev/sdb4": None}
        self.assertEqual(self.disk.name(), expected)
        self.assertEqual(self.disk.partition(), expected)

    def test__linux_disk_name_single(self):
        expected = {"/dev/sdb4": "root"}
        self.assertEqual(self.disk.name(), expected)

    def test__linux_disk_partition_single(self):
        expected = {"/dev/sdb4": "ext4"}
        self.assertEqual(self.disk.partition(), expected)


class TestLinuxDiskMultiple(TestLinuxDisk):

    def setUp(self):
        super(TestLinuxDiskMultiple, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_multiple
        self.run_patch.return_value = self.lsblk_out

    def test__linux_disk_lsblk_not_installed_multiple(self):
        self.which_patch.return_value = False

        expected = {
            "/dev/sdb4": None,
            "/dev/sdb5": None,
        }

        self.assertEqual(self.disk.name(), expected)
        self.assertEqual(self.disk.partition(), expected)

    def test__linux_disk_name_multiple(self):
        expected = {
            "/dev/sdb4": "root",
            "/dev/sdb5": "home",
        }

        self.assertEqual(self.disk.name(), expected)

    def test__linux_disk_partition_multiple(self):
        expected = {
            "/dev/sdb4": "ext4",
            "/dev/sdb5": "ext4",
        }

        self.assertEqual(self.disk.partition(), expected)


class _TestLinuxNetwork(TestLinux):

    def setUp(self):
        super(_TestLinuxNetwork, self).setUp()
        self.net = self.system.query("net")


class TestLinuxNetworkDev(_TestLinuxNetwork):

    def setUp(self):
        super(TestLinuxNetworkDev, self).setUp()
        self.net_original_files = self.net._FILES
        self.net_files_patch = (
            patch("sys_line.systems.linux.Network._FILES",
                  new_callable=PropertyMock).start()
        )

        self.net_dev_glob_patch = patch("sys_line.systems.linux.Path").start()
        self.net_original_files["sys_net"] = self.net_dev_glob_patch
        self.net_files_patch.return_value = self.net_original_files

    @TestLinux.get_open_patch(read_data="up\n")
    def test__linux_net_dev_valid_single(self, mock_file):
        self.net_dev_glob_patch.glob.return_value = (
            Path("/sys/class/net/enp4s0"),
        )
        self.assertEqual(self.net.dev(), "enp4s0")
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/sys/class/net/enp4s0/operstate"), "r"))

    @TestLinux.get_open_patch_multiple(read_datas=("down\n", "up\n", "down\n"))
    def test__linux_net_dev_valid_multiple(self):
        self.net_dev_glob_patch.glob.return_value = (
            Path("/sys/class/net/enp3s0"),
            Path("/sys/class/net/enp4s0"),
            Path("/sys/class/net/enp5s0"),
        )

        self.assertEqual(self.net.dev(), "enp4s0")

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_net_dev_invalid(self, mock_file):
        self.net_dev_glob_patch.glob.return_value = ()
        self.assertEqual(self.net.dev(), None)
        self.assertFalse(mock_file.called)


class TestLinuxNetworkSsid(_TestLinuxNetwork):

    NO_WIFI_FILE = """Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE
 face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22
 """

    # TODO: Add a wifi file
    WIFI_FILE = """"""

    def setUp(self):
        super(TestLinuxNetworkSsid, self).setUp()

        self.net_dev_patch = (
            patch("sys_line.systems.linux.Network.dev").start()
        )

    @TestLinux.get_open_patch(read_data=NO_WIFI_FILE)
    def test__linux_net_ssid_no_wireless(self, mock_file):
        self.net_dev_patch.return_value = "stub"
        self.assertEqual(self.net._ssid(), (None, None))
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        self.assertEqual(args, (Path("/proc/net/wireless"), "r"))

    @TestLinux.get_open_patch(read_data=WIFI_FILE)
    def test__linux_net_ssid_have_wireless(self, mock_file):
        pass

    @TestLinux.get_open_patch(read_data=None)
    def test__linux_net_ssid_dev_invalid(self, mock_file):
        self.net_dev_patch.return_value = None
        self.assertEqual(self.net.dev(), None)
        self.assertEqual(self.net._ssid(), (None, None))
        self.assertFalse(mock_file.called)


class TestLinuxNetwork(_TestLinuxNetwork):

    @TestLinux.get_open_patch(read_data="1000\n")
    def test__linux_net_bytes_delta_up(self, mock_file):
        self.assertEqual(self.net._bytes_delta("stub", "up"), 1000)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        expected = (Path("/sys/class/net/stub/statistics/tx_bytes"), "r")
        self.assertEqual(args, expected)

    @TestLinux.get_open_patch(read_data="1000\n")
    def test__linux_net_bytes_delta_down(self, mock_file):
        self.assertEqual(self.net._bytes_delta("stub", "down"), 1000)
        self.assertTrue(mock_file.called)
        args, _ = mock_file.call_args
        expected = (Path("/sys/class/net/stub/statistics/rx_bytes"), "r")
        self.assertEqual(args, expected)
