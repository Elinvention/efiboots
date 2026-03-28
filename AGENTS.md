# Efiboots Project Overview

Efiboots is a Python-based graphical user interface (GUI) for the `efibootmgr` utility, designed to manage EFI boot loader entries on Linux systems. It allows users to reorder, add, edit, delete, enable, or disable boot entries, as well as set the `BootNext` entry and timeout values.

## Technologies and Architecture

- **Language:** Python 3 (>= 3.10)
- **GUI Toolkit:** GTK 4 (via PyGObject)
- **Core Utility:** `efibootmgr` (versions 17 and 18 supported)
- **Build System:** Meson and Ninja
- **Packaging:** Nix (Flakes and traditional), Flatpak (detected at runtime)
- **Translations:** gettext/i18n support
- **Components:**
    - `src/main.py`: Application entry point and command-line argument handling.
    - `src/window.py`: Main GTK window implementation and business logic for interacting with `efibootmgr`. Handles adding, editing, and removing entries.
    - `src/efibootmgr.py`: Abstraction layer for parsing and executing `efibootmgr` commands.
    - `data/`: Desktop entry, GSchema, icons, and AppStream metadata.

## Building and Running

### Development Environment (Nix)
If you have Nix installed, you can enter a development shell with all dependencies:
```bash
nix-shell
# or
nix develop
```

### Manual Build
1.  **Dependencies:** Ensure `python3`, `efibootmgr`, `gtk4`, `python-gobject`, `meson`, and `ninja` are installed.
2.  **Setup:**
    ```bash
    meson setup build
    ```
3.  **Compile:**
    ```bash
    meson compile -C build
    ```
4.  **Run (Locally):**
    ```bash
    ./build/src/efiboots
    # or
    meson compile -C build run
    ```

### Installation
```bash
meson install -C build
```

### Running with Nix
```bash
nix run .
```

## Testing

The project uses the standard `unittest` framework. Tests are located in the `test/` directory.

To run the tests:
```bash
python3 -m unittest discover test
```

## Development Conventions

- **UI:** Uses `Gtk.Template` with UI files located in `src/gtk/`.
- **System Interaction:** Uses `subprocess` to call `efibootmgr`, `findmnt`, and `lsblk`.
- **Privileges:** Uses `pkexec` to execute commands that require root privileges (like writing to EFI variables).
- **Flatpak:** Code includes logic to detect and handle running inside a Flatpak sandbox (using `flatpak-spawn --host`).
- **Translations:** UI strings are wrapped in `_()` for translation; `.po` files are managed in the `po/` directory.

## Important Files

- `meson.build`: Top-level build configuration.
- `src/efibootmgr.py`: Contains the logic for parsing `efibootmgr` output.
- `src/window.py`: Contains the main application window and logic for managing the boot entries.
- `data/ovh.elinvention.Efiboots.gschema.xml`: GLib settings schema.
- `flake.nix`: Nix Flake definition for the project.
