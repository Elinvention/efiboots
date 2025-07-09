{ pkgs ? import <nixpkgs> { } }:
with pkgs;

let
  pythonPackages = python3Packages;
in
mkShell {
  name = "impurePythonEnv";
  venvDir = "./venv";
  buildInputs = [
    # A Python interpreter including the 'venv' module is required to bootstrap
    # the environment.
    pythonPackages.python

    # This executes some shell code to initialize a venv in $venvDir before
    # dropping into the shell
    pythonPackages.venvShellHook

    # Those are dependencies that we would like to use from nixpkgs, which will
    # add them to PYTHONPATH and thus make them accessible from within the venv.
    pythonPackages.pygobject3

    # In this particular example, in order to compile any binary extensions they may
    # require, the Python modules listed in the hypothetical requirements.txt need
    # the following packages to be installed locally:
    taglib
    openssl
    git
    libxml2
    libxslt
    libzip
    zlib

    efibootmgr
    util-linux

    gobject-introspection
    gtk4
    libadwaita
    glib

    gnome-builder

    # required to compile with gnome builder
    meson
    gettext
    desktop-file-utils
    appstream
    pkg-config
    ninja
    flatpak-builder
  ];

  shellHook = ''
    #export GTK_THEME=Adwaita:dark # Or Adwaita for light theme
    echo "Nix shell with Python, GTK4, and Libadwaita is active!"
  '';
}
