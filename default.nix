with import <nixpkgs> {};
{
  efibootmgr-gui = callPackage ./derivation.nix {};
}
