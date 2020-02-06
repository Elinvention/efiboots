# efibootmgr-gui

Manage EFI boot loader entries with this simple GUI.

## Dependencies

If you are using Debian GNU/Linux:

```
sudo apt install efibootmgr python3
```

Not all distros install **pyhton-gobject** automatically with Python3, but it is required to run this script.

For Arch users:

```
sudo pacman -S efibootmgr python3 python-gobject
```

## Usage

```
python3 efibootmgr_gui.py
# that should be the same as
./efibootmgr_gui.py
```

**Note**: This program assumes that the EFI System Partition (ESP) is mounted at
`/boot/efi`.  
However you can use --efi=/dev/sd?? (e.g. sda1) to manually specify your
EFI System Partition (ESP).
