# efibootmgr-gui

Manage EFI boot loader entries with this simple GUI.

## Dependencies

If you are using Debian GNU/Linux:

```
sudo apt install efibootmgr python3
```

## Usage

Simply run efibootmgr-gui.py and enjoy.

Note: You can use --efi=/dev/sd?? (e.g. sda1) to manually specify your efi partition

Note: This program assumes that the EFI System Partition (ESP) is mounted on
`/boot/efi`.

