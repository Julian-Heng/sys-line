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
#   - Battery tests
#   - Network tests
#   - Misc tests

import unittest

from unittest.mock import MagicMock, PropertyMock, patch

from ..systems.darwin import Darwin
from ..tools.cli import parse_cli


class TestDarwin(unittest.TestCase):

    def setUp(self):
        super(TestDarwin, self).setUp()
        self.system = Darwin(parse_cli([]))

        self.sysctl_patch = patch("sys_line.systems.darwin.Sysctl").start()
        self.which_patch = patch("shutil.which").start()
        self.run_patch = patch("sys_line.systems.darwin.run").start()
        self.time_patch = patch("time.time").start()

    def tearDown(self):
        super(TestDarwin, self).tearDown()
        patch.stopall()


class TestDarwinCpu(TestDarwin):

    def setUp(self):
        super(TestDarwinCpu, self).setUp()
        self.cpu = self.system.query("cpu")

    def test__darwin_cpu_cores(self):
        self.sysctl_patch.query.return_value = "4"
        self.assertEqual(self.cpu.query("cores", None), 4)
        args, _ = self.sysctl_patch.query.call_args
        self.assertEqual(args, ("hw.logicalcpu_max",))

    def test__darwin_cpu_string(self):
        self.sysctl_patch.query.return_value = "Cpu string"
        self.assertEqual(self.cpu._cpu_string(), "Cpu string")
        args, _ = self.sysctl_patch.query.call_args
        self.assertEqual(args, ("machdep.cpu.brand_string",))

    def test__darwin_cpu_speed(self):
        self.assertEqual(self.cpu._cpu_speed(), None)

    def test__darwin_cpu_load_avg(self):
        self.sysctl_patch.query.return_value = "{ 1.27 1.31 1.36 }"
        self.assertEqual(self.cpu._load_avg(),
                         ["1.27", "1.31", "1.36"])
        args, _ = self.sysctl_patch.query.call_args
        self.assertEqual(args, ("vm.loadavg",))

    def test__darwin_cpu_fan_no_prog(self):
        self.which_patch.return_value = False
        self.assertEqual(self.cpu.fan, None)

    def test__darwin_cpu_fan_have_prog_zero_rpm(self):
        self.which_patch.return_value = True

        out = [
            "CPU: 50.1°C",
            "Num fans: 1",
            "Fan 0 - Right Side   at 0 RPM (0%)"
        ]

        self.run_patch.return_value = "\n".join(out)
        self.assertEqual(self.cpu.fan, 0)

    def test__darwin_cpu_fan_have_prog_non_zero_rpm(self):
        self.which_patch.return_value = True

        out = [
            "CPU: 71.2°C",
            "Num fans: 1",
            "Fan 0 - Right Side   at 1359 RPM (28%)"
        ]

        self.run_patch.return_value = "\n".join(out)
        self.assertEqual(self.cpu.fan, 1359)
        self.assertTrue(self.run_patch.called)

    def test__darwin_cpu_temp_no_prog(self):
        self.which_patch.return_value = False
        self.assertEqual(self.cpu.temp, None)

    def test__darwin_cpu_temp_have_prog(self):
        self.which_patch.return_value = True

        out = [
            "CPU: 50.1°C",
            "Num fans: 1",
            "Fan 0 - Right Side   at 0 RPM (0%)"
        ]

        self.run_patch.return_value = "\n".join(out)
        self.assertEqual(self.cpu.temp, 50.1)

    def test__darwin_cpu_uptime(self):
        value = "{ sec = 1594371260, usec = 995858 } Fri Jul 10 16:54:20 2020"
        self.sysctl_patch.query.return_value = value
        self.time_patch.return_value = 1594371300
        self.assertEqual(self.cpu._uptime(), 40)


class TestDarwinMemory(TestDarwin):

    def setUp(self):
        super(TestDarwinMemory, self).setUp()
        self.mem = self.system.query("mem")

    def test__darwin_mem_used(self):
        out = [
            "Mach Virtual Memory Statistics: (page size of 4096 bytes)",
            "Pages free:                             1577393.",
            "Pages active:                           1081107.",
            "Pages inactive:                          672072.",
            "Pages speculative:                       411970.",
            "Pages throttled:                              0.",
            "Pages wired down:                        451416.",
            "Pages purgeable:                         187505.",
            "\"Translation faults\":                 492319022.",
            "Pages copy-on-write:                   80312468.",
            "Pages zero filled:                    145510247.",
            "Pages reactivated:                        19757.",
            "Pages purged:                            720495.",
            "File-backed pages:                       897697.",
            "Anonymous pages:                        1267452.",
            "Pages stored in compressor:                   0.",
            "Pages occupied by compressor:                 0.",
            "Decompressions:                               0.",
            "Compressions:                                 0.",
            "Pageins:                                 748457.",
            "Pageouts:                                     0.",
            "Swapins:                                      0.",
            "Swapouts:                                     0."
        ]

        self.run_patch.return_value = "\n".join(out)
        self.assertEqual(self.mem._used(), (6277214208, "B"))

    def test__darwin_mem_total(self):
        self.sysctl_patch.query.return_value = "17179869184"
        self.assertEqual(self.mem._total(), (17179869184, "B"))
        args, _ = self.sysctl_patch.query.call_args
        self.assertEqual(args, ("hw.memsize",))


class TestDarwinSwap(TestDarwin):

    def setUp(self):
        super(TestDarwinSwap, self).setUp()
        self.swap = self.system.query("swap")
        self.swapusage_mock = patch("sys_line.systems.darwin.Swap.swapusage",
                                    new_callable=PropertyMock).start()

    def test__darwin_swap_used_not_in_use(self):
        ret = "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"
        self.swapusage_mock.return_value = ret
        self.assertEqual(self.swap._used(), (0, "B"))

    def test__darwin_swap_used_in_use(self):
        ret = "total = 2048.00M  used = 100.00M  free = 0.00M  (encrypted)"
        self.swapusage_mock.return_value = ret
        self.assertEqual(self.swap._used(), (104857600, "B"))

    def test__darwin_swap_total_not_in_use(self):
        ret = "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"
        self.swapusage_mock.return_value = ret
        self.assertEqual(self.swap._used(), (0, "B"))

    def test__darwin_swap_total_in_use(self):
        ret = "total = 2048.00M  used = 100.00M  free = 0.00M  (encrypted)"
        self.swapusage_mock.return_value = ret
        self.assertEqual(self.swap._total(), (2147483648, "B"))


class TestDarwinDisk(TestDarwin):

    def setUp(self):
        super(TestDarwinDisk, self).setUp()

        self.disk = self.system.query("disk")

        self.original_dev_mock_single = {
            "/dev/disk1s5": "/dev/disk1s5"
        }

        self.original_dev_mock_multiple = {
            "/dev/disk1s5": "/dev/disk1s5",
            "/dev/disk1s1": "/dev/disk1s1"
        }

        out = [
            # Output of 'diskutil info -plist /dev/disk1s5'
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AESHardware</key>
	<false/>
	<key>APFSContainerFree</key>
	<integer>198511091712</integer>
	<key>APFSContainerReference</key>
	<string>disk1</string>
	<key>APFSContainerSize</key>
	<integer>250790436864</integer>
	<key>APFSPhysicalStores</key>
	<array>
		<dict>
			<key>APFSPhysicalStore</key>
			<string>disk0s2</string>
		</dict>
	</array>
	<key>APFSVolumeGroupID</key>
	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>
	<key>Bootable</key>
	<true/>
	<key>BooterDeviceIdentifier</key>
	<string>disk1s2</string>
	<key>BusProtocol</key>
	<string>PCI</string>
	<key>CanBeMadeBootable</key>
	<false/>
	<key>CanBeMadeBootableRequiresDestroy</key>
	<false/>
	<key>Content</key>
	<string>41504653-0000-11AA-AA11-00306543ECAC</string>
	<key>DeviceBlockSize</key>
	<integer>4096</integer>
	<key>DeviceIdentifier</key>
	<string>disk1s5</string>
	<key>DeviceNode</key>
	<string>/dev/disk1s5</string>
	<key>DeviceTreePath</key>
	<string>IODeviceTree:/PCI0@0/RP06@1C,5/SSD0@0/PRT0@0/PMP@0</string>
	<key>DiskUUID</key>
	<string>A0DB31C6-609F-439A-A883-AD5F057A2A20</string>
	<key>Ejectable</key>
	<false/>
	<key>EjectableMediaAutomaticUnderSoftwareControl</key>
	<false/>
	<key>EjectableOnly</key>
	<false/>
	<key>Encryption</key>
	<true/>
	<key>FileVault</key>
	<true/>
	<key>FilesystemName</key>
	<string>APFS</string>
	<key>FilesystemType</key>
	<string>apfs</string>
	<key>FilesystemUserVisibleName</key>
	<string>APFS</string>
	<key>FreeSpace</key>
	<integer>0</integer>
	<key>Fusion</key>
	<false/>
	<key>GlobalPermissionsEnabled</key>
	<true/>
	<key>IOKitSize</key>
	<integer>250790436864</integer>
	<key>IORegistryEntryName</key>
	<string>Macintosh HD</string>
	<key>Internal</key>
	<true/>
	<key>Locked</key>
	<false/>
	<key>MediaName</key>
	<string></string>
	<key>MediaType</key>
	<string>Generic</string>
	<key>MountPoint</key>
	<string>/</string>
	<key>ParentWholeDisk</key>
	<string>disk1</string>
	<key>PartitionMapPartition</key>
	<false/>
	<key>RAIDMaster</key>
	<false/>
	<key>RAIDSlice</key>
	<false/>
	<key>RecoveryDeviceIdentifier</key>
	<string>disk1s3</string>
	<key>Removable</key>
	<false/>
	<key>RemovableMedia</key>
	<false/>
	<key>RemovableMediaOrExternalDevice</key>
	<false/>
	<key>SMARTDeviceSpecificKeysMayVaryNotGuaranteed</key>
	<dict/>
	<key>SMARTStatus</key>
	<string>Verified</string>
	<key>Size</key>
	<integer>250790436864</integer>
	<key>SolidState</key>
	<true/>
	<key>SupportsGlobalPermissionsDisable</key>
	<true/>
	<key>SystemImage</key>
	<false/>
	<key>TotalSize</key>
	<integer>250790436864</integer>
	<key>VolumeAllocationBlockSize</key>
	<integer>4096</integer>
	<key>VolumeName</key>
	<string>Macintosh HD</string>
	<key>VolumeSize</key>
	<integer>0</integer>
	<key>VolumeUUID</key>
	<string>A0DB31C6-609F-439A-A883-AD5F057A2A20</string>
	<key>WholeDisk</key>
	<false/>
	<key>Writable</key>
	<false/>
	<key>WritableMedia</key>
	<true/>
	<key>WritableVolume</key>
	<false/>
</dict>
</plist>""".split("\n"),
            # Output of 'diskutil info -plist /dev/disk1s1'
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AESHardware</key>
	<false/>
	<key>APFSContainerFree</key>
	<integer>198501175296</integer>
	<key>APFSContainerReference</key>
	<string>disk1</string>
	<key>APFSContainerSize</key>
	<integer>250790436864</integer>
	<key>APFSPhysicalStores</key>
	<array>
		<dict>
			<key>APFSPhysicalStore</key>
			<string>disk0s2</string>
		</dict>
	</array>
	<key>APFSVolumeGroupID</key>
	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>
	<key>Bootable</key>
	<true/>
	<key>BooterDeviceIdentifier</key>
	<string>disk1s2</string>
	<key>BusProtocol</key>
	<string>PCI</string>
	<key>CanBeMadeBootable</key>
	<false/>
	<key>CanBeMadeBootableRequiresDestroy</key>
	<false/>
	<key>Content</key>
	<string>41504653-0000-11AA-AA11-00306543ECAC</string>
	<key>DeviceBlockSize</key>
	<integer>4096</integer>
	<key>DeviceIdentifier</key>
	<string>disk1s1</string>
	<key>DeviceNode</key>
	<string>/dev/disk1s1</string>
	<key>DeviceTreePath</key>
	<string>IODeviceTree:/PCI0@0/RP06@1C,5/SSD0@0/PRT0@0/PMP@0</string>
	<key>DiskUUID</key>
	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>
	<key>Ejectable</key>
	<false/>
	<key>EjectableMediaAutomaticUnderSoftwareControl</key>
	<false/>
	<key>EjectableOnly</key>
	<false/>
	<key>Encryption</key>
	<true/>
	<key>FileVault</key>
	<true/>
	<key>FilesystemName</key>
	<string>APFS</string>
	<key>FilesystemType</key>
	<string>apfs</string>
	<key>FilesystemUserVisibleName</key>
	<string>APFS</string>
	<key>FreeSpace</key>
	<integer>0</integer>
	<key>Fusion</key>
	<false/>
	<key>GlobalPermissionsEnabled</key>
	<true/>
	<key>IOKitSize</key>
	<integer>250790436864</integer>
	<key>IORegistryEntryName</key>
	<string>Macintosh HD — Data</string>
	<key>Internal</key>
	<true/>
	<key>Locked</key>
	<false/>
	<key>MediaName</key>
	<string></string>
	<key>MediaType</key>
	<string>Generic</string>
	<key>MountPoint</key>
	<string>/System/Volumes/Data</string>
	<key>ParentWholeDisk</key>
	<string>disk1</string>
	<key>PartitionMapPartition</key>
	<false/>
	<key>RAIDMaster</key>
	<false/>
	<key>RAIDSlice</key>
	<false/>
	<key>RecoveryDeviceIdentifier</key>
	<string>disk1s3</string>
	<key>Removable</key>
	<false/>
	<key>RemovableMedia</key>
	<false/>
	<key>RemovableMediaOrExternalDevice</key>
	<false/>
	<key>SMARTDeviceSpecificKeysMayVaryNotGuaranteed</key>
	<dict/>
	<key>SMARTStatus</key>
	<string>Verified</string>
	<key>Size</key>
	<integer>250790436864</integer>
	<key>SolidState</key>
	<true/>
	<key>SupportsGlobalPermissionsDisable</key>
	<true/>
	<key>SystemImage</key>
	<false/>
	<key>TotalSize</key>
	<integer>250790436864</integer>
	<key>VolumeAllocationBlockSize</key>
	<integer>4096</integer>
	<key>VolumeName</key>
	<string>Macintosh HD — Data</string>
	<key>VolumeSize</key>
	<integer>0</integer>
	<key>VolumeUUID</key>
	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>
	<key>WholeDisk</key>
	<false/>
	<key>Writable</key>
	<true/>
	<key>WritableMedia</key>
	<true/>
	<key>WritableVolume</key>
	<true/>
</dict>
</plist>""".split("\n")
        ]

        self.diskutil_mock_multiple = ["\n".join(i) for i in out]
        self.diskutil_mock_single = self.diskutil_mock_multiple[0]

        self.dev_patch = patch("sys_line.systems.darwin.Disk.original_dev",
                               new_callable=PropertyMock).start()


class TestDarwinDiskDiskutil(TestDarwinDisk):

    def setUp(self):
        super(TestDarwinDiskDiskutil, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_multiple
        self.run_patch.side_effect = self.diskutil_mock_multiple

    def test__darwin_disk_diskutil(self):
        diskutil = self.disk._diskutil
        entry = next(iter(diskutil.values()))

        self.assertTrue(diskutil is not None)
        self.assertTrue(isinstance(entry, dict))


class TestDarwinDiskSingle(TestDarwinDisk):

    def setUp(self):
        super(TestDarwinDiskSingle, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_single
        self.run_patch.return_value = self.diskutil_mock_single

    def test__darwin_disk_name_single(self):
        expected = {"/dev/disk1s5": "Macintosh HD"}
        self.assertEqual(self.disk.name, expected)

    def test__darwin_disk_partition_single(self):
        expected = {"/dev/disk1s5": "APFS"}
        self.assertEqual(self.disk.partition, expected)


class TestDarwinDiskMultiple(TestDarwinDisk):

    def setUp(self):
        super(TestDarwinDiskMultiple, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_multiple
        self.run_patch.side_effect = self.diskutil_mock_multiple

    def test__darwin_disk_name_multiple(self):
        expected = {
            "/dev/disk1s5": "Macintosh HD",
            "/dev/disk1s1": "Macintosh HD — Data"
        }

        self.assertEqual(self.disk.name, expected)

    def test__darwin_disk_partition_multiple(self):
        expected = {
            "/dev/disk1s5": "APFS",
            "/dev/disk1s1": "APFS"
        }

        self.assertEqual(self.disk.partition, expected)
