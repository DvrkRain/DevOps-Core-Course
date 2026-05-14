# Lab 18 — DevOps Info Service (Nix build)

This directory is the working copy of the [Lab 1 / Lab 2 FastAPI app](../../../app_python) used for [Lab 18 — Reproducible Builds with Nix](../../lab18.md). The source code is identical to `app_python/`; only the build artifacts (`default.nix`, `docker.nix`, `flake.nix`) are new.

See [`../../submission18.md`](../../submission18.md) for the full lab write-up, hashes, comparison tables, and reflections.

## Quick start (requires Nix, e.g. inside WSL2 on Windows)

```bash
# Task 1 — build the app reproducibly
nix-build                                   # produces ./result
./result/bin/devops-info-service            # runs the service on :5000
readlink result                             # /nix/store/<hash>-devops-info-service-1.0.0
nix-hash --type sha256 result               # bit-for-bit fingerprint

# Task 2 — build a reproducible Docker image
nix-build docker.nix                        # produces a tarball at ./result
sha256sum result                            # identical across builds
docker load < result                        # imports devops-info-service-nix:1.0.0
docker run -d -p 5001:5000 \
  --name nix-container devops-info-service-nix:1.0.0

# Bonus — modern Nix with flakes
nix flake update                            # generates flake.lock
nix build                                   # default package
nix build .#dockerImage                     # docker image via flake
nix develop                                 # enter dev shell (replaces pip + venv)
```

## File map

| File                  | Purpose                                                                    |
| --------------------- | -------------------------------------------------------------------------- |
| `src/app.py`          | FastAPI service (copied verbatim from `app_python/src/app.py`)             |
| `requirements.txt`    | Lab 1 dependency list — kept for the `pip`-vs-Nix comparison               |
| `Dockerfile`          | Lab 2 traditional Dockerfile — kept to demonstrate non-reproducibility     |
| `docker-compose.yml`  | Lab 2 compose file — for running the traditional image side-by-side        |
| `tests/`              | pytest suite (still works inside `nix develop`)                            |
| `default.nix`         | **Task 1** — Nix derivation that builds the app via `buildPythonApplication` |
| `docker.nix`          | **Task 2** — Nix `dockerTools.buildLayeredImage` for a reproducible image  |
| `flake.nix`           | **Bonus** — Modern flake exposing `default`, `dockerImage`, `devShells`    |
| `flake.lock`          | **Bonus** — Cryptographically pinned dependency graph (generated)          |

## Notes

- `DATA_DIR` is overridden to `/tmp/devops-info-service-data` by the Nix wrapper because the Nix store is read-only and the app writes a visit counter file. Inside the Docker image, `DATA_DIR=/data` (an empty directory created at image-build time).
- Test/lint dependencies (`pytest`, `pytest-cov`, `httpx`, `ruff`) are intentionally **not** in the runtime closure — they are only available in `nix develop` to keep the production artifact minimal.
- All Nix expressions are pure and sandboxed: no network access, no host filesystem reads outside this directory.
