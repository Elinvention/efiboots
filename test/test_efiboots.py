import unittest
import logging

from pathlib import Path

import efiboots

logging.basicConfig(level=0)
test_dir = Path(__file__).resolve().parent


class TestDeviceToDiskPart(unittest.TestCase):
    def test_device_to_disk_part(self):
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/sda1'), ('/dev/sda', '1'))
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/sdc13'), ('/dev/sdc', '13'))
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/sdp3'), ('/dev/sdp', '3'))
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/sdp10'), ('/dev/sdp', '10'))
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/mmcblk1p2'), ('/dev/mmcblk1', '2'))
        self.assertTupleEqual(efiboots.device_to_disk_part('/dev/nvme0n1p1'), ('/dev/nvme0n1', '1'))


class TestEfibootmgrDecode(unittest.TestCase):
    def test_decode(self):
        decoded = efiboots.try_decode_efibootmgr('B.C.D.O.B.J.E.C.T.=.{.9.d.e.a.8.6.2.c.-.5.c.d.d.-.4.e.7.0.-.a.c.c.1.-.f.3.2.b.3.4.4.d.4.7.9.5.}.')
        expected = 'BCDOBJECT={9dea862c-5cdd-4e70-acc1-f32b344d4795}'
        self.assertEqual(decoded, expected)


class TestParser(unittest.TestCase):
    def test_efibootmgr_entries_parsing(self):
        key, value = efiboots.parse_efibootmgr_line('Boot0000* SATA1 : Samsung SSD 850 PRO 25\tBBS(17,,0x0)')
        self.assertEqual(key, 'entry')
        self.assertDictEqual(value, {'num': '0000', 'active': True,
                                     'name': 'SATA1 : Samsung SSD 850 PRO 25',
                                     'path': '', 'parameters': ''})
        key, value = efiboots.parse_efibootmgr_line('Boot0001* rEFInd Boot Manager\tHD(1,GPT,fda4f976-b250-4569-be80-0449804ab7c2,0x800,0x40000)/File(\EFI\refind\refind_x64.efi)')
        self.assertEqual(key, 'entry')
        self.assertDictEqual(value, {'num': '0001', 'active': True,
                                     'name': 'rEFInd Boot Manager',
                                     'path': '\\EFI\refind\refind_x64.efi',
                                     'parameters': ''})
        key, value = efiboots.parse_efibootmgr_line('Boot0004  linux-surface (reboot=pci)	HD(1,GPT,8b824cbb-3248-4aeb-8ca0-3073b5a41bc4,0x800,0x82000)/File(\\vmlinuz-linux-surface)r.o.o.t.=.L.A.B.E.L.=.r.o.o.t. .i.n.i.t.r.d.=.i.n.t.e.l.-.u.c.o.d.e...i.m.g. .i.n.i.t.r.d.=.i.n.i.t.r.a.m.f.s.-.l.i.n.u.x.-.s.u.r.f.a.c.e...i.m.g. .z.s.w.a.p...e.n.a.b.l.e.d.=.0. .r.e.b.o.o.t.=.p.c.i.')
        self.assertEqual(key, 'entry')
        self.assertDictEqual(value, {'num': '0004', 'active': False, 'name': ' linux-surface (reboot=pci)',
                                    'path': '\\vmlinuz-linux-surface',
                                    'parameters': 'root=LABEL=root initrd=intel-ucode.img initrd=initramfs-linux-surface.img zswap.enabled=0 reboot=pci'})

    def test_efibootmgr_bootcurrent_parsing(self):
        key, value = efiboots.parse_efibootmgr_line('BootCurrent: 0001')
        self.assertEqual(key, 'boot_current')
        self.assertEqual(value, '0001')

    def test_efibootmgr_timeout_parsing(self):
        key, value = efiboots.parse_efibootmgr_line('Timeout: 1 seconds')
        self.assertEqual(key, 'timeout')
        self.assertEqual(value, 1)

    def test_efibootmgr_bootorder_parsing(self):
        key, value = efiboots.parse_efibootmgr_line('BootOrder: 0001,0003,0005,0000,0002,0004')
        self.assertEqual(key, 'boot_order')
        self.assertListEqual(value, ['0001', '0003', '0005', '0000', '0002', '0004'])
