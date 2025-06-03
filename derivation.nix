{
  lib,
  gtk4,
  glib,
  gobject-introspection,
  efibootmgr,
  python3,
  util-linux,
  wrapGAppsHook,
  desktop-file-utils,
  hicolor-icon-theme,
  meson,
  ninja,
  pkg-config,
  gettext,
  appstream,
  stdenv,
  ...
}:

let
  python_deps = with python3.pkgs; [
    pygobject3
  ];
in
stdenv.mkDerivation (finalAttrs: {
  name = "efiboots";
  src = lib.cleanSource ./.;

  nativeBuildInputs = [
    meson
    ninja
    pkg-config
    gettext
    appstream
    wrapGAppsHook
    python3.pkgs.wrapPython
    desktop-file-utils # needed for update-desktop-database
    glib # needed for glib-compile-schemas
    gobject-introspection # need for gtk namespace to be available
    hicolor-icon-theme # needed for postinstall script
    efibootmgr
    util-linux
  ];

  buildInputs = [
    gtk4
    glib
  ];

  propagatedBuildInputs = python_deps;

  doCheck = true;
  checkInputs = finalAttrs.buildInputs;

  # ModuleNotFoundError: No module named 'gi' error
  # fix found from https://github.com/NixOS/nixpkgs/issues/343134#issuecomment-2453502399
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
  '';
  postFixup = ''
    wrapPythonPrograms
  '';

  meta = {
    description = " Manage EFI boot loader entries with this simple GUI";
    homepage = "https://github.com/Elinvention/efibootmgr-gui";
    license = lib.licenses.gpl3;
    platforms = lib.platforms.linux;
  };
})
