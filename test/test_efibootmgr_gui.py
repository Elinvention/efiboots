import unittest
import logging

import efibootmgr_gui

logging.basicConfig(level=0)


class TestDeviceToDiskPart(unittest.TestCase):
    def test_device_to_disk_part(self):
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/sda1'), ('/dev/sda', '1'))
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/sdc13'), ('/dev/sdc', '13'))
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/sdp3'), ('/dev/sdp', '3'))
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/sdp10'), ('/dev/sdp', '10'))
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/mmcblk1p2'), ('/dev/mmcblk1', '2'))
        self.assertTupleEqual(efibootmgr_gui.device_to_disk_part('/dev/nvme0n1p1'), ('/dev/nvme0n1', '1'))


class TestGUI(unittest.TestCase):
    def test_efibootmgr_parsing(self):
        with open('myinput.test') as f:
            parsed = efibootmgr_gui.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'loader': None},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager',
                     'loader': '\\EFI\\refind\\refind_x64.efi'},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'loader': None},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager',
                     'loader': '\\EFI\\Microsoft\\Boot\\bootmgfw.efi'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'loader': None},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'loader': '\\EFI\\BOOT\\BOOTX64.EFI'},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'loader': '\\EFI\\Manjaro\\grubx64.efi'}],
                'boot_order': ['0001', '0007', '0003', '0005', '0000', '0002', '0004'],
                'boot_next': None,
                'boot_current': '0001',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
        with open('mycraftedinput.test') as f:
            parsed = efibootmgr_gui.parse_efibootmgr(f)
            expected = {
                'entries': [
                    {'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'loader': None},
                    {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager',
                     'loader': '\\EFI\\refind\\refind_x64.efi'},
                    {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'loader': None},
                    {'num': '0003', 'active': True, 'name': 'Windows Boot Manager',
                     'loader': '\\EFI\\Microsoft\\Boot\\bootmgfw.efi'},
                    {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'loader': None},
                    {'num': '0005', 'active': True, 'name': 'UEFI OS', 'loader': '\\EFI\\BOOT\\BOOTX64.EFI'},
                    {'num': '0007', 'active': True, 'name': 'Manjaro', 'loader': '\\EFI\\Manjaro\\grubx64.efi'}],
                'boot_order': ['0001', '0003', '0005', '0000', '0002', '0004'],
                'boot_next': None,
                'boot_current': '0001',
                'timeout': 1
            }
            self.assertDictEqual(parsed, expected)
        with open('mycraftedinput2.test') as f:
            parsed = efibootmgr_gui.parse_efibootmgr(f)
            expected = {
                'entries': [{'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'loader': None},
                            {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager',
                             'loader': '\\EFI\\refind\\refind_x64.efi'},
                            {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'loader': None},
                            {'num': '0003', 'active': True, 'name': 'Windows Boot Manager',
                             'loader': '\\EFI\\Microsoft\\Boot\\bootmgfw.efi'},
                            {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'loader': None},
                            {'num': '0005', 'active': True, 'name': 'UEFI OS', 'loader': '\\EFI\\BOOT\\BOOTX64.EFI'},
                            {'num': '0007', 'active': True, 'name': 'Manjaro',
                             'loader': '\\EFI\\Manjaro\\grubx64.efi'}],
                'boot_order': ['0001', '0003', '0005', '0000', '0002', '0004', '000A'], 'boot_next': None,
                'boot_current': '0001', 'timeout': 1}
            self.assertDictEqual(parsed, expected)
        with open('mycraftedinput3.test') as f:
            parsed = efibootmgr_gui.parse_efibootmgr(f)
            expected = {
                'entries': [{'num': '0000', 'active': True, 'name': 'SATA1 : Samsung SSD 850 PRO 25', 'loader': None},
                            {'num': '0001', 'active': True, 'name': 'rEFInd Boot Manager',
                             'loader': '\\EFI\\refind\\refind_x64.efi'},
                            {'num': '0002', 'active': True, 'name': 'Mass Storage Device ', 'loader': None},
                            {'num': '0003', 'active': True, 'name': 'Windows Boot Manager',
                             'loader': '\\EFI\\Microsoft\\Boot\\bootmgfw.efi'},
                            {'num': '0004', 'active': False, 'name': ' UEFI: Built-in EFI Shell ', 'loader': None},
                            {'num': '0005', 'active': True, 'name': 'UEFI OS', 'loader': '\\EFI\\BOOT\\BOOTX64.EFI'},
                            {'num': '0007', 'active': True, 'name': 'Manjaro',
                             'loader': '\\EFI\\Manjaro\\grubx64.efi'}],
                'boot_order': ['0001', '0007', '0003', '0005', '0000', '0002', '0004'], 'boot_next': None,
                'boot_current': '000A', 'timeout': 1}
            self.assertDictEqual(parsed, expected)
