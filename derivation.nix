{ lib, gtk4, glib, gobject-introspection, efibootmgr, python3, util-linux
, wrapGAppsHook, desktop-file-utils, hicolor-icon-theme }:

let
  python_deps = with python3.pkgs; [
    pygobject3
  ];
in
python3.pkgs.buildPythonApplication rec {
  name = "efiboots";
  src = ./.;

  nativeBuildInputs = [
    wrapGAppsHook
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
  checkInputs = buildInputs;

  meta = with lib; {
    description = " Manage EFI boot loader entries with this simple GUI";
    homepage = "https://github.com/Elinvention/efibootmgr-gui";
    license = licenses.gpl3;
    platforms = platforms.linux;
  };
}
