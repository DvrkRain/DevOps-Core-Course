# Lab 18 — Bonus Task
#
# Modern Nix flake wrapping default.nix + docker.nix.
#
# Why a flake?
#   * `flake.lock` cryptographically pins nixpkgs, so the *entire* dependency
#     graph (Python, FastAPI, glibc, OpenSSL, ld, gcc, …) is locked in version
#     control. Compare with Lab 10's values.yaml, which only pins the image tag.
#   * Builds on Linux (incl. WSL2), Intel Mac, and Apple Silicon out of the box
#     via `flake-utils.lib.eachDefaultSystem` — no manual `system = ...` edit.
#
# Usage:
#   nix flake update       # generate / refresh flake.lock
#   nix build              # build the default package (== default.nix)
#   nix build .#dockerImage  # build the OCI tarball (== docker.nix)
#   nix run                # build + run the app
#   nix develop            # drop into a reproducible dev shell
{
  description = "DevOps Info Service — Reproducible Build (Lab 18)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        app = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      in {
        packages = {
          default = app;
          devops-info-service = app;
          dockerImage = dockerImage;
        };

        apps = {
          default = {
            type = "app";
            program = "${app}/bin/devops-info-service";
          };
          devops-info-service = {
            type = "app";
            program = "${app}/bin/devops-info-service";
          };
        };

        # Reproducible dev shell — the modern replacement for
        # `python -m venv venv && pip install -r requirements.txt`.
        # Same Python, same package versions, on every machine, forever.
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Runtime stack (matches default.nix propagatedBuildInputs)
            python3
            python3Packages.fastapi
            python3Packages.uvicorn
            python3Packages.python-json-logger
            python3Packages.prometheus-client
            python3Packages.python-dotenv

            # Dev-only tooling — intentionally absent from the runtime closure
            python3Packages.pytest
            python3Packages.pytest-cov
            python3Packages.httpx
            ruff
          ];

          shellHook = ''
            export DATA_DIR="$PWD/.data"
            mkdir -p "$DATA_DIR"
            echo ""
            echo "Lab 18 — reproducible dev shell ready"
            echo "  python: $(python --version)"
            echo "  fastapi: $(python -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null)"
            echo "  uvicorn: $(python -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null)"
            echo "  DATA_DIR=$DATA_DIR"
            echo ""
            echo "Try:  pytest tests/ -v"
            echo "      python src/app.py"
            echo ""
          '';
        };

        # `nix flake check` will validate that the flake outputs build.
        checks = {
          build = app;
        };
      });
}
