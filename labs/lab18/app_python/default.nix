# Lab 18 — Task 1
#
# Nix derivation that builds the Lab 1 / Lab 2 DevOps Info Service (FastAPI)
# reproducibly. Same inputs → identical /nix/store/<hash>-... path on any
# machine, any time.
#
# Build:
#   nix-build
# Run:
#   ./result/bin/devops-info-service
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";

  # Use the whole lab18 app_python/ directory as the source so that src/,
  # requirements.txt, Dockerfile, etc. are all available to the build sandbox.
  src = ./.;

  # The repo has no setup.py / pyproject.toml — use the freeform builder.
  format = "other";

  # Disable the default `check` phase: pytest needs httpx + pytest, which are
  # dev-only and intentionally not propagated into the runtime closure. The
  # test suite is still runnable via `nix develop` (see flake.nix).
  doCheck = false;

  # Runtime dependencies — every package in requirements.txt that is actually
  # imported at runtime. Versions are pinned by nixpkgs, not requirements.txt.
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    python-json-logger
    prometheus-client
    python-dotenv
  ];

  # makeWrapper is needed to produce a self-contained launcher that has the
  # right PYTHONPATH, working directory, and DATA_DIR baked in.
  nativeBuildInputs = [ pkgs.makeWrapper ];

  # Custom install phase because format = "other":
  #   - copy src/* into $out/lib/devops-info-service so `from app import ...`
  #     and uvicorn.run("app:app", ...) inside app.py still resolve correctly;
  #   - wrap a launcher in $out/bin/devops-info-service that invokes the
  #     pinned Python with all the deps from propagatedBuildInputs visible.
  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib/devops-info-service $out/bin
    cp -r src/* $out/lib/devops-info-service/

    makeWrapper ${pkgs.python3}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/lib/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$out/lib/devops-info-service:$PYTHONPATH" \
      --chdir "$out/lib/devops-info-service" \
      --set-default DATA_DIR /tmp/devops-info-service-data

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "DevOps Info Service — FastAPI app, reproducibly built with Nix";
    homepage = "https://github.com/DvrkRain/DevOps-Core-Course";
    license = licenses.mit;
    platforms = platforms.linux ++ platforms.darwin;
    mainProgram = "devops-info-service";
  };
}
