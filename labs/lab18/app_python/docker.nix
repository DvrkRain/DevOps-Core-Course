# Lab 18 — Task 2
#
# Reproducible OCI image built from the same derivation as Task 1.
# Unlike `docker build` against a Dockerfile, this produces a bit-for-bit
# identical tarball on every machine and at every point in time.
#
# Build:
#   nix-build docker.nix
# Load into Docker:
#   docker load < result
# Run:
#   docker run -d -p 5001:5000 \
#     --name nix-container devops-info-service-nix:1.0.0
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  # Everything that ends up inside the image.
  #   - `app` brings in /bin/devops-info-service, Python, and the whole
  #     transitive closure of FastAPI/uvicorn/etc.
  #   - coreutils + bash are useful for `docker exec ... sh` debugging without
  #     bloating the closure significantly.
  contents = [
    app
    pkgs.coreutils
    pkgs.bash
  ];

  # Pre-create /data inside the rootfs so the visit-counter file can be
  # written without mounting a host volume. Permissions are deterministic.
  extraCommands = ''
    mkdir -p data tmp
    chmod 777 data tmp
  '';

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];

    ExposedPorts = {
      "5000/tcp" = {};
    };

    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "DEBUG=False"
      "DATA_DIR=/data"
      "PATH=/bin"
    ];

    WorkingDir = "/";

    Labels = {
      "org.opencontainers.image.title" = "devops-info-service";
      "org.opencontainers.image.version" = "1.0.0";
      "org.opencontainers.image.source" =
        "https://github.com/DvrkRain/DevOps-Core-Course";
      "org.opencontainers.image.description" =
        "DevOps Info Service — built reproducibly with Nix dockerTools";
    };
  };

  # The single most important line for reproducibility: pin the image
  # creation time to a fixed epoch instead of `now`. Without this, two
  # builds of the same docker.nix yield different sha256 hashes.
  created = "1970-01-01T00:00:01Z";
}
