with import <nixpkgs> {};
{
  efiboots = callPackage ./derivation.nix {};
}
