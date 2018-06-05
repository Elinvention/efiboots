# efibootmgr-gui

Manage EFI boot loader entries with this simple GUI.

## Dependencies

If you are using Debian GNU/Linux:

```
sudo apt install efibootmgr python3
```

## Usage

```
python3 efibootmgr-gui.py
# that should be the same as
./efibootmgr-gui.py
```

**Note**: This program assumes that the EFI System Partition (ESP) is mounted at
`/boot/efi`.  
However you can use --efi=/dev/sd?? (e.g. sda1) to manually specify your
EFI System Partition (ESP).
