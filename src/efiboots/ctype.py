"""
This program was a prototype to try avoid efibootmgr parsing pitfalls by directly
reading efivars from python thanks to ctypes.

It is not currently used by Efiboots. 
"""
import sys
import struct
import uuid
import ctypes
import ctypes.util

from typing import Union, List, Optional, Tuple
from ctypes import byref, POINTER, c_void_p, c_int, c_char_p, c_ssize_t, c_uint32, c_uint16, c_uint8


def swap16(i):
    return struct.unpack("<H", struct.pack(">H", i))[0]


path_libc = ctypes.util.find_library("c")
efiboot_path = ctypes.util.find_library("efiboot")
efivar_path = ctypes.util.find_library("efivar")

try:
    libc = ctypes.CDLL(path_libc)
    efiboot = ctypes.CDLL(efiboot_path)
    efivar = ctypes.CDLL(efivar_path)
except OSError as exc:
    print("Unable to load C library")
    print(exc)
    sys.exit()


class EfiGuid(ctypes.Structure):
    """
    typedef struct {
        uint32_t	a;
        uint16_t	b;
        uint16_t	c;
        uint16_t	d;
        uint8_t		e[6];
    } efi_guid_t __attribute__((__aligned__(1)));
    """
    _fields_ = [
        ('a', c_uint32),
        ('b', c_uint16),
        ('c', c_uint16),
        ('d', c_uint16),
        ('e', c_uint8 * 6)
    ]

    def __str__(self):
        # define GUID_FORMAT "%08x-%04x-%04x-%04x-%02x%02x%02x%02x%02x%02x"
        last = ''.join(('{:02x}'.format(e) for e in self.e))
        return f'{self.a:08x}-{self.b:04x}-{self.c:04x}-{swap16(self.d):04x}-{last}'

    def __repr__(self):
        return f'<EfiGuid {self.__str__()}>'


class EfiVariable(ctypes.Structure):
    """
    struct efi_variable {
        uint64_t attrs;
        efi_guid_t *guid;
        unsigned char *name;
        uint8_t *data;
        size_t data_size;
    };
    """
    _fields_ = [
        ('attrs', ctypes.c_uint64),
        ('guid', ctypes.POINTER(EfiGuid)),
        ('name', ctypes.c_char_p),
        ('data', ctypes.POINTER(ctypes.c_uint8)),
        ('data', ctypes.c_size_t),
    ]


EfiVariable_p = POINTER(EfiVariable)
EfiGuid_p = POINTER(EfiGuid)

# efi_variable_get_name = efivar.efi_variable_get_name
# efi_variable_get_name.argtypes = [EfiVariable_p]
# efi_variable_get_name.restype = ctypes.c_char_p

# efi_variable_alloc = efivar.efi_variable_alloc
# efi_variable_alloc.argtypes = []
# efi_variable_alloc.restype = EfiVariable_p

efi_variables_supported = efivar.efi_variables_supported
efi_variables_supported.argtypes = []
efi_variables_supported.restype = ctypes.c_int

assert efi_variables_supported() == 1

# int efi_get_variable(efi_guid_t guid, const char *name,
#                            void **data, ssize_t *data_size,
#                            uint32_t *attributes);

efi_get_variable = efivar.efi_get_variable
efi_get_variable.argtypes = [EfiGuid, c_char_p, c_void_p, POINTER(c_ssize_t), POINTER(c_uint32)]
efi_get_variable.restype = c_int

# int efi_get_next_variable_name(efi_guid_t **guid, char **name)
efi_get_next_variable_name = efivar.efi_get_next_variable_name
efi_get_next_variable_name.argtypes = [POINTER(EfiGuid_p), POINTER(c_char_p)]
efi_get_next_variable_name.restype = c_int

# int efi_str_to_guid(const char *s, efi_guid_t *guid);
efi_str_to_guid = efivar.efi_str_to_guid
efi_str_to_guid.argtypes = [ctypes.c_char_p, EfiGuid_p]
efi_str_to_guid.restype = ctypes.c_int


def get_variable_data(var_name: str, guid_str="8be4df61-93ca-11d2-aa0d-00e098032b8c") -> Union[None, bytes]:
    try:
        with open(f'/sys/firmware/efi/efivars/{var_name}-{guid_str}', 'rb') as f:
            var_data = f.read()
            var_attributes = int.from_bytes(var_data[0:4], 'little')
            return var_data[4:], var_attributes
    except FileNotFoundError:
        return None, None

    c_guid = EfiGuid()
    got = efi_str_to_guid(guid_str.encode(), byref(c_guid))
    if got != 0:
        return None

    data = ctypes.c_void_p(None)
    data_size = ctypes.c_ssize_t()
    attributes = ctypes.c_uint32()

    got = efi_get_variable(c_guid, var_name.encode(), byref(data), byref(data_size), byref(attributes))
    if got != 0:
        return None

    data_bytes = ctypes.string_at(data, data_size.value)
    print(var_name, data_size.value, data_bytes)

    return data_bytes


def get_load_option_attributes(data_bytes: bytes) -> List[str]:
    attrs = []
    attr = int.from_bytes(data_bytes[0:4], 'little')
    if attr & 0b001:
        attrs.append('active')
    if attr & 0b010:
        attrs.append('force reconnect')
    if attr & 0b100:
        attrs.append('hidden')
    if attr & 0x1F00:
        attrs.append('category')
    return attrs


def get_load_option_description(data_bytes: bytes) -> Tuple[str, int]:
    desc_end = data_bytes.find(b'\x00\x00', 6)
    if data_bytes[desc_end + 2] == 0:
        desc_end += 1
    desc_bytes = data_bytes[6:desc_end]
    desc = desc_bytes.decode('utf-16')
    return desc, desc_end + 2


def parse_device_path(device_type: int, device_sub: int, length: int, device_path_bytes: bytes):
    if device_type == 4:
        if device_sub == 1:
            num, start, size, sig, fmt, sigtype = struct.unpack('<IQQ16sBB', device_path_bytes)
            if fmt == 2 and sigtype == 2:
                sig = uuid.UUID(bytes_le=sig)
            return 'HDD', num, start, size, sig, 'GPT' if fmt == 2 else 'MBR', sigtype
        if device_sub == 2:
            boot_entry, start, size = struct.unpack('<IQQ', device_path_bytes)
            return 'CDROM', boot_entry, start, size
        if device_sub == 3:
            vendor_guid, vendor_data = struct.unpack(f'<16s{length-20}s', device_path_bytes)
            return 'Vendor', uuid.UUID(bytes_le=vendor_guid), vendor_data
        if device_sub == 4:
            path_name = device_path_bytes.decode('utf-16')
            return 'File path', path_name
        return f"Unknown subtype {device_type}:{device_sub}"
    if device_type == 5:
        bios_device_type, bios_status_flag, bios_description = struct.unpack(f'<HH{length-8}s', device_path_bytes)
        return 'BIOS', bios_device_type, bios_status_flag, bios_description.decode('ascii')
    return f"Unknown type {device_type}:{device_sub}"


def get_load_option_device_path(data_bytes: bytes, start_byte: int):
    device_type = 0x00
    device_paths = []
    while device_type != 0x7f:  # TODO: differentiate between sub_type 0xff and 0x01
        common_header_bytes = data_bytes[start_byte:start_byte+4]
        device_type, device_sub, length = struct.unpack('<BBH', common_header_bytes)
        if device_type != 0x7f:
            device_paths.append(parse_device_path(device_type, device_sub, length, data_bytes[start_byte+4:start_byte+length]))
        start_byte += length

    return device_paths, start_byte


def get_load_option_optional_data(data_bytes: bytes, start_byte: int):
    optional_bytes = data_bytes[start_byte:]
    if optional_bytes.startswith(b'WINDOWS'):
        return optional_bytes.decode('Windows-1252')
    return optional_bytes


def list_variables(guid_str='8be4df61-93ca-11d2-aa0d-00e098032b8c') -> List[str]:
    guid = EfiGuid_p()
    name = c_char_p(None)
    names = []
    while efi_get_next_variable_name(byref(guid), byref(name)) > 0:
        if str(guid[0]) == guid_str and name.value:
            names.append(name.value.decode())
    return names


def get_boot_current() -> int:
    data, _ = get_variable_data('BootCurrent')
    return int.from_bytes(data, 'little')


def get_boot_next() -> Optional[int]:
    data, _ = get_variable_data('BootNext')
    if data:
        return int.from_bytes(data, 'little')


def get_boot_order() -> Tuple[int]:
    data, _ = get_variable_data('BootOrder')
    values = len(data) // 2
    order = struct.unpack(f'<{values}H', data)
    return order


def get_timeout() -> int:
    data, _ = get_variable_data('Timeout')
    return int.from_bytes(data, 'little')


print(f"BootCurrent: Boot{get_boot_current():04X}")
boot_next = get_boot_next()
print(f"NextBoot: Boot{boot_next:04X}" if boot_next else "BootNext: None")
print(f"Timeout: {get_timeout()}")
print(f"BootOrder: {', '.join(('{:04X}'.format(o) for o in get_boot_order()))}")

variables = [v for v in list_variables() if v.startswith('Boot0')]
for var in sorted(variables):
    var_data, var_attr = get_variable_data(var)
    if var_data:
        load_opt_attr = get_load_option_attributes(var_data)
        var_desc, next_field = get_load_option_description(var_data)
        path, next_field = get_load_option_device_path(var_data, next_field)
        optional = get_load_option_optional_data(var_data, next_field)
        if 'active' in load_opt_attr:
            var += '*'
        print(f'{var}: "{var_desc}" {path} {optional}')
