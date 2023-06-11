import abc
import logging
import re
import subprocess


class Efibootmgr(abc.ABC):
    version_regex = re.compile(r'version ([0-9]+)')
    parse_line_regex = re.compile(r'^Boot([0-9A-F]+)(\*)? (.+)\t(?:.+/File\((.+)\)|.*\))(.*)$')
    log = logging.getLogger('Efibootmgr')

    @staticmethod
    def get_version() -> str:
        output = subprocess.run(["efibootmgr", "--version"], check=True, capture_output=True, text=True).stdout
        matched = Efibootmgr.version_regex.match(output)
        version = matched.group(1)
        Efibootmgr.log.info("efibootmgr version %s detected", version)
        return version

    @staticmethod
    def get_instance() -> 'Efibootmgr':
        version = Efibootmgr.get_version()
        match version:
            case "17":
                return EfibootmgrV17()
            case "18":
                return EfibootmgrV18()
            case _:
                raise NotImplementedError(f"efibootmgr version {version} is not supported")

    @abc.abstractmethod
    def run(self) -> list[str]:
        pass

    @staticmethod
    @abc.abstractmethod
    def parse_line(line: str) -> tuple[str, object]:
        pass

    @classmethod
    def parse(cls, boot: list[str]) -> dict:
        parser_logger = logging.getLogger("parser")
        parsed_efi = {
            'entries': [],
            'boot_order': [],
            'boot_next': None,
            'boot_current': None,
            'timeout': None
        }

        for line in boot:
            try:
                key, value = cls.parse_line(line)
                if key == 'entry':
                    parsed_efi['entries'].append(value)
                else:
                    parsed_efi[key] = value
            except ValueError as e:
                parser_logger.warning("line didn't match: %s", e.args[1])

        return parsed_efi


class EfibootmgrV17(Efibootmgr):
    def run(self) -> list[str]:
        output = subprocess.run(["efibootmgr", "-v"], check=True, capture_output=True,
                                text=True).stdout.strip().split('\n')
        logging.debug(repr(output))
        return output

    @staticmethod
    def decode_params(code: str) -> str:
        if '.' not in code:
            return code
        if code.endswith('.') and code.count('.') == 1:
            return code
        if code.startswith('WINDOWS'):
            return 'WINDOWS' + EfibootmgrV17.decode_params(code[len('WINDOWS'):])
        try:
            # Decode as UTF-16 (why efibootmgr displays it like that?)
            code_bytes = bytearray(code, 'utf-8')
            for i, byte in enumerate(code_bytes):
                if i % 2 == 1 and byte == ord('.'):
                    code_bytes[i] = 0
            decoded = code_bytes.decode('utf-16')
            return decoded
        except UnicodeDecodeError as e:
            logging.warning("Could not decode '%s': %s", code, e)
            return code

    @staticmethod
    def parse_line(line: str) -> tuple[str, object]:
        parser_logger = logging.getLogger("parser")
        match = Efibootmgr.parse_line_regex.match(line)

        if match and match.group(1) and match.group(3):
            num, active, name, path, params = match.groups()
            params = EfibootmgrV17.decode_params(params)
            parsed = dict(num=num, active=active is not None, name=name,
                          path=path if path else '', parameters=params)
            parser_logger.debug("Entry: %s", parsed)
            return 'entry', parsed
        if line.startswith("BootOrder"):
            parsed = line.split(':')[1].strip().split(',')
            parser_logger.debug("BootOrder: %s", parsed)
            return 'boot_order', parsed
        if line.startswith("BootNext"):
            parsed = line.split(':')[1].strip()
            parser_logger.debug("BootNext: %s", parsed)
            return 'boot_next', parsed
        if line.startswith("BootCurrent"):
            parsed = line.split(':')[1].strip()
            parser_logger.debug("BootCurrent: %s", parsed)
            return 'boot_current', parsed
        if line.startswith("Timeout"):
            parsed = int(line.split(':')[1].split()[0].strip())
            parser_logger.debug("Timeout: %s", parsed)
            return 'timeout', parsed

        raise ValueError("line didn't match", repr(line))


class EfibootmgrV18(Efibootmgr):
    def run(self):
        output = subprocess.run(["efibootmgr", "--unicode"], check=True, capture_output=True,
                                text=True).stdout.strip().split('\n')
        logging.debug(repr(output))
        return output

    @staticmethod
    def parse_line(line: str) -> tuple[str, object]:
        parser_logger = logging.getLogger("parser")
        match = Efibootmgr.parse_line_regex.match(line)

        if match and match.group(1) and match.group(3):
            num, active, name, path, params = match.groups()
            parsed = dict(num=num, active=active is not None, name=name,
                          path=path if path else '', parameters=params)
            parser_logger.debug("Entry: %s", parsed)
            return 'entry', parsed
        if line.startswith("BootOrder"):
            parsed = line.split(':')[1].strip().split(',')
            parser_logger.debug("BootOrder: %s", parsed)
            return 'boot_order', parsed
        if line.startswith("BootNext"):
            parsed = line.split(':')[1].strip()
            parser_logger.debug("BootNext: %s", parsed)
            return 'boot_next', parsed
        if line.startswith("BootCurrent"):
            parsed = line.split(':')[1].strip()
            parser_logger.debug("BootCurrent: %s", parsed)
            return 'boot_current', parsed
        if line.startswith("Timeout"):
            parsed = int(line.split(':')[1].split()[0].strip())
            parser_logger.debug("Timeout: %s", parsed)
            return 'timeout', parsed

        raise ValueError("line didn't match", repr(line))
