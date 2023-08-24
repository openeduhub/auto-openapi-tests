{
  description = "An automatic testing suite for OpenAPI services";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    nix-filter.url = "github:numtide/nix-filter";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # import the packages from nixpkgs
        pkgs = import nixpkgs {
          inherit system;
          # enable if unfree software is required
          config.allowUnfree = false;
        };
        nix-filter = self.inputs.nix-filter.lib;
        # the python version we are using
        python = pkgs.python310;

        ### create the python installation for the package
        python-packages-build = py-pkgs:
          with py-pkgs; [
            hypothesis
            pytest
            openapi-spec-validator
            requests
          ];

        ### create the python installation for development
        # the development installation contains all build packages,
        # plus some additional ones we do not need to include in production.
        python-packages-devel = py-pkgs:
          with py-pkgs;
          [ ipython jupyter black pyflakes isort ]
          ++ (python-packages-build py-pkgs);

        ### create the python package
        python-package = python.pkgs.buildPythonPackage {
          pname = "auto-openapi-tests";
          version = "0.1.0";
          /* only include files that are related to the package.
             this will prevent unnecessary rebuilds
          */
          src = nix-filter {
            root = self;
            include = [
              # folders
              "auto_openapi_tests"
              # files
              ./setup.py
              ./requirements.txt
            ];
            exclude = [ (nix-filter.matchExt "pyc") ];
          };
          propagatedBuildInputs = (python-packages-build python.pkgs);
        };

      in rec {
        # the packages that we can build
        packages = {
          default = python-package;
        };
        # the development environment
        devShells.default = pkgs.mkShell {
          buildInputs = [
            # the development installation of python
            (python.withPackages python-packages-devel)
            # python lsp server
            pkgs.nodePackages.pyright
            # for automatically generating nix expressions, e.g. from PyPi
            pkgs.nix-template
            pkgs.nix-init
          ];
        };
      });
}
