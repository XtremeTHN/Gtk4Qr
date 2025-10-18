{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python3 = (
        pkgs.python313.withPackages (
          ps: with ps; [
            pygobject3
            opencv4
          ]
        )
      );

      nativeBuildInputs = with pkgs; [
        python3
        meson
        ninja
        pkg-config
        wrapGAppsHook4
        gobject-introspection
      ];
      buildInputs = with pkgs; [
        glib
        gtk4
        libadwaita
      ];
    in
    {

      devShells.${system}.default = pkgs.mkShell {
        inherit buildInputs;
        nativeBuildInputs = nativeBuildInputs ++ [
          python3.pkgs.pygobject-stubs
        ];
        packages = with pkgs; [
          d-spy
        ];
      };

      packages.${system}.default = pkgs.stdenv.mkDerivation {
        name = "dbusqrdecoder";
        versin = "0.1";
        src = ./.;

        inherit nativeBuildInputs buildInputs;
      };
    };
}
