import logging
import re
import subprocess
import os

device_regex = re.compile(r'^([a-z/]+[0-9a-z]*?)p?([0-9]+)$')


def is_in_flatpak():
    return "FLATPAK_ID" in os.environ


def subprocess_run_wrapper(cmd):
    if is_in_flatpak():
        cmd = ["flatpak-spawn", "--host"] + cmd
        logging.debug("Flatpak sandbox detected. Running: %s", ' '.join(cmd))
    else:
        logging.debug("Running: %s", ' '.join(cmd))
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def device_to_disk_part(device: str) -> tuple[str, str] | None:
    match = device_regex.match(device)
    if match:
        return match.groups()
    return None


def make_auto_detect_esp_with_findmnt(esp_mount_point):
    def auto_detect_esp_with_findmnt() -> tuple[str, str] | None:
        cmd = ["findmnt", "--noheadings", "--output", "SOURCE,FSTYPE", "--mountpoint", esp_mount_point]
        try:
            findmnt_output = subprocess_run_wrapper(cmd)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            logging.warning("Could not detect ESP with findmnt: %s", e)
            return None
        splitted = findmnt_output.strip().split()
        for source, fstype in zip(splitted[::2], splitted[1::2]):
            if fstype == 'vfat':
                return device_to_disk_part(source)
        return None
    return auto_detect_esp_with_findmnt


def auto_detect_esp_with_lsblk(error_callback=None) -> tuple[str, str] | None:
    esp_part_types = ('C12A7328-F81F-11D2-BA4B-00A0C93EC93B', 'EF')
    cmd = ['lsblk', '--noheadings', '--pairs', '--paths', '--output', 'NAME,PARTTYPE,FSTYPE']
    try:
        res = subprocess_run_wrapper(cmd).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.warning("Could not detect ESP with lsblk: %s", e)
        return None
    regex = re.compile('^NAME="(.+)" PARTTYPE="(.+)" FSTYPE="(.+)"$', re.MULTILINE)
    esps = []
    for match in regex.finditer(res):
        name, part_type, fs_type = match.groups()
        if part_type.upper() in esp_part_types and fs_type == 'vfat':
            esps.append(name)
    if len(esps) == 0:
        return None
    if len(esps) == 1:
        return device_to_disk_part(esps[0])
    if error_callback:
        error_callback(esps)
    return None


def auto_detect_esp(error_callback=None) -> tuple[str, str] | tuple[None, None]:
    methods = (make_auto_detect_esp_with_findmnt('/efi'),
               make_auto_detect_esp_with_findmnt('/boot/efi'),
               make_auto_detect_esp_with_findmnt('/boot'),
               lambda: auto_detect_esp_with_lsblk(error_callback))
    for find_esp_method in methods:
        result = find_esp_method()
        if result:
            disk, part = result
            logging.info("Detected ESP on disk %s part %s", disk, part)
            return disk, part
    logging.fatal("Can't auto-detect ESP! All methods failed.")
    return None, None
