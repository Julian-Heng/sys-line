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

# TODO:
#   - Memory tests
#   - Swap tests
#   - Disk tests
#   - Battery tests
#   - Network tests
#   - Misc tests

import unittest

from pathlib import Path as p
from unittest.mock import MagicMock, PropertyMock, patch

from ..systems.linux import Linux
from ..tools.cli import parse_cli


class TestLinux(unittest.TestCase):

    def setUp(self):
        super(TestLinux, self).setUp()
        self.system = Linux(parse_cli([]))

        self.open_read_patch = (
            patch("sys_line.systems.linux.open_read").start()
        )
        self.run_patch = patch("sys_line.systems.linux.run").start()

    def tearDown(self):
        super(TestLinux, self).tearDown()
        patch.stopall()


class TestLinuxCpu(TestLinux):

    def setUp(self):
        super(TestLinuxCpu, self).setUp()
        self.cpu = self.system.query("cpu")

        self.cpu_file_patch = patch("sys_line.systems.linux.Cpu._cpu_file",
                                    new_callable=PropertyMock).start()
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

        self.cpu_file_patch.return_value = """
processor       : 0
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

    def test__linux_cpu_cores(self):
        self.assertEqual(self.cpu.query("cores", None), 4)

    def test__linux_cpu_string(self):
        self.assertEqual(self.cpu._cpu_string(),
                         "Intel(R) Core(TM) i5-4590 CPU @ 3.30GHz")

    def test__linux_cpu_speed_valid(self):
        self.cpu_speed_file_path_patch.return_value = "stub"
        self.open_read_patch.return_value = "3700000\n"
        self.assertEqual(self.cpu._cpu_speed(), 3.7)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, ("stub",))

    def test__linux_cpu_speed_invalid(self):
        self.cpu_speed_file_path_patch.return_value = None
        self.assertEqual(self.cpu._cpu_speed(), None)

    def test__linux_load_avg_valid(self):
        self.open_read_patch.return_value = "1.06 1.09 1.15 2/996 281756\n"
        self.assertEqual(self.cpu._load_avg(), ["1.06", "1.09", "1.15"])
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, (p("/proc/loadavg"),))

    def test__linux_load_avg_invalid(self):
        self.open_read_patch.return_value = None
        self.assertEqual(self.cpu._load_avg(), None)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, (p("/proc/loadavg"),))

    def test__linux_fan_valid(self):
        self.cpu_fan_file_path_patch.return_value = "stub"
        self.open_read_patch.return_value = "1234\n"
        self.assertEqual(self.cpu.fan, 1234)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, ("stub",))

    def test__linux_fan_invalid(self):
        self.cpu_fan_file_path_patch.return_value = None
        self.assertEqual(self.cpu.fan, None)
        self.assertEqual(self.open_read_patch.call_args, None)

    def test__linux_temp_valid(self):
        self.cpu_temp_file_paths_patch.return_value = ["stub1", "stub2"]
        self.open_read_patch.return_value = "58000\n"
        self.assertEqual(self.cpu.temp, 58.0)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, ("stub1",))

    def test__linux_temp_invalid(self):
        self.cpu_temp_file_paths_patch.return_value = None
        self.assertEqual(self.cpu.temp, None)
        self.assertEqual(self.open_read_patch.call_args, None)

    def test__linux_uptime_valid(self):
        self.open_read_patch.return_value = "45516.13 123925.62\n"
        self.assertEqual(self.cpu._uptime(), 45516)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, (p("/proc/uptime"),))

    def test__linux_uptime_invalid(self):
        self.open_read_patch.return_value = None
        self.assertEqual(self.cpu._uptime(), None)
        args, _ = self.open_read_patch.call_args
        self.assertEqual(args, (p("/proc/uptime"),))
