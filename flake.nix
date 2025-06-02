{
  description = "Efiboots nix flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages.${system}; in
      {
        devShells.default = import ./shell.nix { inherit pkgs; };

        packages = rec {
          efiboots = pkgs.callPackage ./derivation.nix { inherit pkgs; };
          default = efiboots;
        };
      }
    );

}
