#!/usr/bin/env python3

import unittest

from unittest.mock import MagicMock, PropertyMock, patch

from ..systems.darwin import Darwin
from ..tools.cli import parse_cli


class TestDarwin(unittest.TestCase):

    def setUp(self):
        super(TestDarwin, self).setUp()
        self.system = Darwin(parse_cli([]))
        self.system.aux.sysctl = MagicMock()


class TestDarwinCpu(TestDarwin):

    def test__darwin_cpu_cores(self):
        self.system.aux.sysctl.query.return_value = "4"
        self.assertEqual(self.system.cpu.cores, 4)
        self.assertEqual(self.system.aux.sysctl.query.call_args.args,
                         ("hw.logicalcpu_max",))

    def test__darwin_cpu_speed(self):
        self.system.aux.sysctl.query.return_value = "Cpu string"
        self.assertEqual(self.system.cpu._cpu_speed(), ("Cpu string", None))
        self.assertEqual(self.system.aux.sysctl.query.call_args.args,
                         ("machdep.cpu.brand_string",))

    def test__darwin_cpu_load_avg(self):
        self.system.aux.sysctl.query.return_value = "{ 1.27 1.31 1.36 }"
        self.assertEqual(self.system.cpu._load_avg(),
                         ["1.27", "1.31", "1.36"])
        self.assertEqual(self.system.aux.sysctl.query.call_args.args,
                         ("vm.loadavg",))

    def test__darwin_cpu_fan(self):
        with patch("shutil.which", return_value=False):
            self.assertEqual(self.system.cpu.fan, None)

        with patch("shutil.which", return_value=True) as which_patch, \
             patch("sys_line.systems.darwin.run") as run_patch:

            out = [
                "CPU: 50.1°C",
                "Num fans: 1",
                "Fan 0 - Right Side   at 0 RPM (0%)"
            ]

            run_patch.return_value = "\n".join(out)
            self.assertEqual(self.system.cpu.fan, 0)

        with patch("shutil.which", return_value=True) as which_patch, \
             patch("sys_line.systems.darwin.run") as run_patch:

            out = [
                "CPU: 71.2°C",
                "Num fans: 1",
                "Fan 0 - Right Side   at 1359 RPM (28%)"
            ]

            run_patch.return_value = "\n".join(out)
            self.assertEqual(self.system.cpu.fan, 1359)
            self.assertEqual(run_patch.called, True)

    def test__darwin_cpu_temp(self):
        with patch("shutil.which", return_value=False):
            self.assertEqual(self.system.cpu.temp, None)

        with patch("shutil.which", return_value=True) as which_patch, \
             patch("sys_line.systems.darwin.run") as run_patch:

            out = [
                "CPU: 50.1°C",
                "Num fans: 1",
                "Fan 0 - Right Side   at 0 RPM (0%)"
            ]

            run_patch.return_value = "\n".join(out)
            self.assertEqual(self.system.cpu.temp, 50.1)

    def test__darwin_cpu_uptime(self):
        value = "{ sec = 1594371260, usec = 995858 } Fri Jul 10 16:54:20 2020"
        self.system.aux.sysctl.query.return_value = value

        with patch("time.time", return_value=1594371300):
            self.assertEqual(self.system.cpu._uptime(), 40)


class TestDarwinMemory(TestDarwin):

    def test__darwin_mem_used(self):
        with patch("sys_line.systems.darwin.run") as run_patch:
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

            run_patch.return_value = "\n".join(out)
            self.assertEqual(self.system.mem._used(), (6277214208, "B"))

    def test__darwin_mem_total(self):
        self.system.aux.sysctl.query.return_value = "17179869184"
        self.assertEqual(self.system.mem._total(), (17179869184, "B"))
        self.assertEqual(self.system.aux.sysctl.query.call_args.args,
                         ("hw.memsize",))


class TestDarwinSwap(TestDarwin):

    def test__darwin_swap_used(self):
        with patch("sys_line.systems.darwin.Swap.swapusage",
                   new_callable=PropertyMock) as swapusage_mock:
            ret = "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"
            swapusage_mock.return_value = ret
            self.assertEqual(self.system.swap._used(), (0, "B"))

        with patch("sys_line.systems.darwin.Swap.swapusage",
                   new_callable=PropertyMock) as swapusage_mock:
            ret = "total = 2048.00M  used = 100.00M  free = 0.00M  (encrypted)"
            swapusage_mock.return_value = ret
            self.assertEqual(self.system.swap._used(), (104857600, "B"))

    def test__darwin_swap_total(self):
        with patch("sys_line.systems.darwin.Swap.swapusage",
                   new_callable=PropertyMock) as swapusage_mock:
            ret = "total = 0.00M  used = 0.00M  free = 0.00M  (encrypted)"
            swapusage_mock.return_value = ret
            self.assertEqual(self.system.swap._used(), (0, "B"))

        with patch("sys_line.systems.darwin.Swap.swapusage",
                   new_callable=PropertyMock) as swapusage_mock:
            ret = "total = 2048.00M  used = 100.00M  free = 0.00M  (encrypted)"
            swapusage_mock.return_value = ret
            self.assertEqual(self.system.swap._total(), (2147483648, "B"))


class TestDarwinDisk(TestDarwin):

    def setUp(self):
        super(TestDarwinDisk, self).setUp()

        self.original_dev_mock_single = {
            "/dev/disk1s5": "/dev/disk1s5"
        }

        self.original_dev_mock_multiple = {
            "/dev/disk1s5": "/dev/disk1s5",
            "/dev/disk1s1": "/dev/disk1s1"
        }

        out = [
            [
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
                "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
                "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">",
                "<plist version=\"1.0\">",
                "<dict>",
                "	<key>AESHardware</key>",
                "	<false/>",
                "	<key>APFSContainerFree</key>",
                "	<integer>198572486656</integer>",
                "	<key>APFSContainerReference</key>",
                "	<string>disk1</string>",
                "	<key>APFSContainerSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>APFSPhysicalStores</key>",
                "	<array>",
                "		<dict>",
                "			<key>APFSPhysicalStore</key>",
                "			<string>disk0s2</string>",
                "		</dict>",
                "	</array>",
                "	<key>APFSVolumeGroupID</key>",
                "	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>",
                "	<key>Bootable</key>",
                "	<true/>",
                "	<key>BooterDeviceIdentifier</key>",
                "	<string>disk1s2</string>",
                "	<key>BusProtocol</key>",
                "	<string>PCI</string>",
                "	<key>CanBeMadeBootable</key>",
                "	<false/>",
                "	<key>CanBeMadeBootableRequiresDestroy</key>",
                "	<false/>",
                "	<key>Content</key>",
                "	<string>41504653-0000-11AA-AA11-00306543ECAC</string>",
                "	<key>DeviceBlockSize</key>",
                "	<integer>4096</integer>",
                "	<key>DeviceIdentifier</key>",
                "	<string>disk1s5</string>",
                "	<key>DeviceNode</key>",
                "	<string>/dev/disk1s5</string>",
                "	<key>DeviceTreePath</key>",
                "	<string>IODeviceTree:"
                "/PCI0@0/RP06@1C,5/SSD0@0/PRT0@0/PMP@0</string>",
                "	<key>DiskUUID</key>",
                "	<string>A0DB31C6-609F-439A-A883-AD5F057A2A20</string>",
                "	<key>Ejectable</key>",
                "	<false/>",
                "	<key>EjectableMediaAutomaticUnderSoftwareControl</key>",
                "	<false/>",
                "	<key>EjectableOnly</key>",
                "	<false/>",
                "	<key>Encryption</key>",
                "	<true/>",
                "	<key>FileVault</key>",
                "	<true/>",
                "	<key>FilesystemName</key>",
                "	<string>APFS</string>",
                "	<key>FilesystemType</key>",
                "	<string>apfs</string>",
                "	<key>FilesystemUserVisibleName</key>",
                "	<string>APFS</string>",
                "	<key>FreeSpace</key>",
                "	<integer>0</integer>",
                "	<key>Fusion</key>",
                "	<false/>",
                "	<key>GlobalPermissionsEnabled</key>",
                "	<true/>",
                "	<key>IOKitSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>IORegistryEntryName</key>",
                "	<string>Macintosh HD</string>",
                "	<key>Internal</key>",
                "	<true/>",
                "	<key>Locked</key>",
                "	<false/>",
                "	<key>MediaName</key>",
                "	<string></string>",
                "	<key>MediaType</key>",
                "	<string>Generic</string>",
                "	<key>MountPoint</key>",
                "	<string>/</string>",
                "	<key>ParentWholeDisk</key>",
                "	<string>disk1</string>",
                "	<key>PartitionMapPartition</key>",
                "	<false/>",
                "	<key>RAIDMaster</key>",
                "	<false/>",
                "	<key>RAIDSlice</key>",
                "	<false/>",
                "	<key>RecoveryDeviceIdentifier</key>",
                "	<string>disk1s3</string>",
                "	<key>Removable</key>",
                "	<false/>",
                "	<key>RemovableMedia</key>",
                "	<false/>",
                "	<key>RemovableMediaOrExternalDevice</key>",
                "	<false/>",
                "	<key>SMARTDeviceSpecificKeysMayVaryNotGuaranteed</key>",
                "	<dict/>",
                "	<key>SMARTStatus</key>",
                "	<string>Verified</string>",
                "	<key>Size</key>",
                "	<integer>250790436864</integer>",
                "	<key>SolidState</key>",
                "	<true/>",
                "	<key>SupportsGlobalPermissionsDisable</key>",
                "	<true/>",
                "	<key>SystemImage</key>",
                "	<false/>",
                "	<key>TotalSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>VolumeAllocationBlockSize</key>",
                "	<integer>4096</integer>",
                "	<key>VolumeName</key>",
                "	<string>Macintosh HD</string>",
                "	<key>VolumeSize</key>",
                "	<integer>0</integer>",
                "	<key>VolumeUUID</key>",
                "	<string>A0DB31C6-609F-439A-A883-AD5F057A2A20</string>",
                "	<key>WholeDisk</key>",
                "	<false/>",
                "	<key>Writable</key>",
                "	<false/>",
                "	<key>WritableMedia</key>",
                "	<true/>",
                "	<key>WritableVolume</key>",
                "	<false/>",
                "</dict>",
                "</plist>"
            ],
            [
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
                "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
                "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">",
                "<plist version=\"1.0\">",
                "<dict>",
                "	<key>AESHardware</key>",
                "	<false/>",
                "	<key>APFSContainerFree</key>",
                "	<integer>198560165888</integer>",
                "	<key>APFSContainerReference</key>",
                "	<string>disk1</string>",
                "	<key>APFSContainerSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>APFSPhysicalStores</key>",
                "	<array>",
                "		<dict>",
                "			<key>APFSPhysicalStore</key>",
                "			<string>disk0s2</string>",
                "		</dict>",
                "	</array>",
                "	<key>APFSVolumeGroupID</key>",
                "	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>",
                "	<key>Bootable</key>",
                "	<true/>",
                "	<key>BooterDeviceIdentifier</key>",
                "	<string>disk1s2</string>",
                "	<key>BusProtocol</key>",
                "	<string>PCI</string>",
                "	<key>CanBeMadeBootable</key>",
                "	<false/>",
                "	<key>CanBeMadeBootableRequiresDestroy</key>",
                "	<false/>",
                "	<key>Content</key>",
                "	<string>41504653-0000-11AA-AA11-00306543ECAC</string>",
                "	<key>DeviceBlockSize</key>",
                "	<integer>4096</integer>",
                "	<key>DeviceIdentifier</key>",
                "	<string>disk1s1</string>",
                "	<key>DeviceNode</key>",
                "	<string>/dev/disk1s1</string>",
                "	<key>DeviceTreePath</key>",
                "	<string>IODeviceTree"
                ":/PCI0@0/RP06@1C,5/SSD0@0/PRT0@0/PMP@0</string>",
                "	<key>DiskUUID</key>",
                "	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>",
                "	<key>Ejectable</key>",
                "	<false/>",
                "	<key>EjectableMediaAutomaticUnderSoftwareControl</key>",
                "	<false/>",
                "	<key>EjectableOnly</key>",
                "	<false/>",
                "	<key>Encryption</key>",
                "	<true/>",
                "	<key>FileVault</key>",
                "	<true/>",
                "	<key>FilesystemName</key>",
                "	<string>APFS</string>",
                "	<key>FilesystemType</key>",
                "	<string>apfs</string>",
                "	<key>FilesystemUserVisibleName</key>",
                "	<string>APFS</string>",
                "	<key>FreeSpace</key>",
                "	<integer>0</integer>",
                "	<key>Fusion</key>",
                "	<false/>",
                "	<key>GlobalPermissionsEnabled</key>",
                "	<true/>",
                "	<key>IOKitSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>IORegistryEntryName</key>",
                "	<string>Macintosh HD — Data</string>",
                "	<key>Internal</key>",
                "	<true/>",
                "	<key>Locked</key>",
                "	<false/>",
                "	<key>MediaName</key>",
                "	<string></string>",
                "	<key>MediaType</key>",
                "	<string>Generic</string>",
                "	<key>MountPoint</key>",
                "	<string>/System/Volumes/Data</string>",
                "	<key>ParentWholeDisk</key>",
                "	<string>disk1</string>",
                "	<key>PartitionMapPartition</key>",
                "	<false/>",
                "	<key>RAIDMaster</key>",
                "	<false/>",
                "	<key>RAIDSlice</key>",
                "	<false/>",
                "	<key>RecoveryDeviceIdentifier</key>",
                "	<string>disk1s3</string>",
                "	<key>Removable</key>",
                "	<false/>",
                "	<key>RemovableMedia</key>",
                "	<false/>",
                "	<key>RemovableMediaOrExternalDevice</key>",
                "	<false/>",
                "	<key>SMARTDeviceSpecificKeysMayVaryNotGuaranteed</key>",
                "	<dict/>",
                "	<key>SMARTStatus</key>",
                "	<string>Verified</string>",
                "	<key>Size</key>",
                "	<integer>250790436864</integer>",
                "	<key>SolidState</key>",
                "	<true/>",
                "	<key>SupportsGlobalPermissionsDisable</key>",
                "	<true/>",
                "	<key>SystemImage</key>",
                "	<false/>",
                "	<key>TotalSize</key>",
                "	<integer>250790436864</integer>",
                "	<key>VolumeAllocationBlockSize</key>",
                "	<integer>4096</integer>",
                "	<key>VolumeName</key>",
                "	<string>Macintosh HD — Data</string>",
                "	<key>VolumeSize</key>",
                "	<integer>0</integer>",
                "	<key>VolumeUUID</key>",
                "	<string>34544CD1-0205-44F3-885C-7E1C28DAE1BB</string>",
                "	<key>WholeDisk</key>",
                "	<false/>",
                "	<key>Writable</key>",
                "	<true/>",
                "	<key>WritableMedia</key>",
                "	<true/>",
                "	<key>WritableVolume</key>",
                "	<true/>",
                "</dict>",
                "</plist>"
            ]
        ]

        self.diskutil_mock_multiple = ["\n".join(i) for i in out]
        self.diskutil_mock_single = self.diskutil_mock_multiple[0]

        self.dev_patch = patch("sys_line.systems.darwin.Disk.original_dev",
                               new_callable=PropertyMock).start()
        self.run_patch = patch("sys_line.systems.darwin.run").start()

    def tearDown(self):
        super(TestDarwinDisk, self).tearDown()
        patch.stopall()


class TestDarwinDiskDiskutil(TestDarwinDisk):

    def setUp(self):
        super(TestDarwinDiskDiskutil, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_multiple
        self.run_patch.side_effect = self.diskutil_mock_multiple

    def test__darwin_disk_diskutil(self):
        diskutil = self.system.disk.diskutil
        entry = next(iter(diskutil.values()))

        self.assertEqual(diskutil is not None, True)
        self.assertEqual(isinstance(entry, dict), True)


class TestDarwinDiskSingle(TestDarwinDisk):

    def setUp(self):
        super(TestDarwinDiskSingle, self).setUp()
        self.dev_patch.return_value = self.original_dev_mock_single
        self.run_patch.return_value = self.diskutil_mock_single

    def test__darwin_disk_name_single(self):
        expected = {"/dev/disk1s5": "Macintosh HD"}
        self.assertEqual(self.system.disk.name, expected)

    def test__darwin_disk_partition_single(self):
        expected = {"/dev/disk1s5": "APFS"}
        self.assertEqual(self.system.disk.partition, expected)


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

        self.assertEqual(self.system.disk.name, expected)

    def test__darwin_disk_partition_multiple(self):
        expected = {
            "/dev/disk1s5": "APFS",
            "/dev/disk1s1": "APFS"
        }

        self.assertEqual(self.system.disk.partition, expected)
