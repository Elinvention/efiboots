{
  description = "Efiboots nix flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
    flake-compat.url = "github:edolstra/flake-compat";
  };

  outputs =
    {
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = import ./nix/shell.nix { inherit pkgs; };
        packages = rec {
          efiboots = pkgs.callPackage ./nix/package.nix { };
          default = efiboots;
        };
      }
    );
}
