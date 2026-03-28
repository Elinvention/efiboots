from .utils import device_to_disk_part
from .efibootmgr import EfibootmgrV17

def try_decode_efibootmgr(code: str) -> str:
    return EfibootmgrV17.decode_params(code)

def parse_efibootmgr_line(line: str) -> tuple[str, object]:
    # For tests, we use V17 parser as it seems what they expect
    try:
        key, value = EfibootmgrV17.parse_line(line)
        if key == 'entry':
            # Convert dataclass to dict for compatibility with old tests
            return key, {
                'num': value.num,
                'active': value.active,
                'name': value.name,
                'path': value.path,
                'parameters': value.parameters
            }
        return key, value
    except ValueError:
        raise
