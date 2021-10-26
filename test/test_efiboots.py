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


class TestGUI(unittest.TestCase):
    def test_efibootmgr_parsing(self):
        with open(test_dir / 'myinput.test') as f:
            parsed = efiboots.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'path': None, 'parameters': ''},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager', 'path': None, 'parameters': ''},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'path': None, 'parameters': ''},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager', 'path': None, 'parameters': 'WINDOWS....x.BCDOBJECT={9dea862c-5cdd-4e70-acc1-f32b344d4795}.o......\x7f.'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'path': None, 'parameters': 'AMBO'},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'path': None, 'parameters': ''},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'path': None, 'parameters': ''}
                ],
                'boot_order': ['0001', '0007', '0003', '0005', '0000', '0002', '0004'],
                'boot_next': None,
                'boot_current': '0001',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
        with open(test_dir / 'mycraftedinput.test') as f:
            parsed = efiboots.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'path': None, 'parameters': ''},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager', 'path': None, 'parameters': ''},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'path': None, 'parameters': ''},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager', 'path': None, 'parameters': 'WINDOWS....x.BCDOBJECT={9dea862c-5cdd-4e70-acc1-f32b344d4795}.o......\x7f.'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'path': None, 'parameters': 'AMBO'},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'path': None, 'parameters': ''},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'path': None, 'parameters': ''}
                ],
                'boot_order': ['0001', '0003', '0005', '0000', '0002', '0004'],
                'boot_next': None,
                'boot_current': '0001',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
        with open(test_dir / 'mycraftedinput2.test') as f:
            parsed = efiboots.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'path': None, 'parameters': ''},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager', 'path': None, 'parameters': ''},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'path': None, 'parameters': ''},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager', 'path': None, 'parameters': 'WINDOWS....x.BCDOBJECT={9dea862c-5cdd-4e70-acc1-f32b344d4795}.o......\x7f.'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'path': None, 'parameters': 'AMBO'},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'path': None, 'parameters': ''},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'path': None, 'parameters': ''}
                ],
                'boot_order': ['0001', '0003', '0005', '0000', '0002', '0004', '000A'],
                'boot_next': None,
                'boot_current': '0001',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
        with open(test_dir / 'mycraftedinput3.test') as f:
            parsed = efiboots.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'path': None, 'parameters': ''},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager', 'path': None, 'parameters': ''},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'path': None, 'parameters': ''},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager', 'path': None, 'parameters': 'WINDOWS....x.BCDOBJECT={9dea862c-5cdd-4e70-acc1-f32b344d4795}.o......\x7f.'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'path': None, 'parameters': 'AMBO'},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'path': None, 'parameters': ''},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'path': None, 'parameters': ''}
                ],
                'boot_order': ['0001', '0007', '0003', '0005', '0000', '0002', '0004'],
                'boot_next': None,
                'boot_current': '000A',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
