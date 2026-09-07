# Run the Toolchain in a Container

An alternative to [installing the toolchain](install-test-build.md) on your machine. The
image carries `uv`, `just`, Python 3.12 and the dev dependency group, so every `just` recipe
runs without Python, uv or just being present on the host.

This is a **development environment, not a shipping artifact**. The package is published as a
wheel built from `pyproject.toml`; nothing in the image takes part in that build.

## Requirements

- **Docker** with the Compose plugin (`docker compose version`)
- The repository cloned locally — the image supplies the environment, your working tree
  supplies the code

## Build

```bash
docker compose build
```

The container runs as a non-root user so that files a recipe creates (`docs-build`'s
`site/`, a new `generate-domain` directory, coverage's `htmlcov/`, ...) come back owned by
you, not root, on the bind-mounted host tree. It defaults to uid/gid `1000`, the common
single-account Linux default; build with your own to match exactly:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose build
```

If you skip this and your account's ids differ from `1000`, files the container writes are
still yours to read, but not to overwrite or delete without `sudo` — rebuilding with the
right ids, or running `docker compose run --rm ontology-tools chown -R $(id -u):$(id -g) /workspace`
after the fact, both fix it.

## Run

`compose.yaml` bind-mounts the repository at `/workspace`, so edits on the host are visible
immediately and generated artifacts land back in your working tree.

```bash
# Interactive shell with the toolchain
docker compose run --rm ontology-tools

# Any recipe, without entering a shell
docker compose run --rm ontology-tools just --list
docker compose run --rm ontology-tools just lint
docker compose run --rm ontology-tools just test
docker compose run --rm ontology-tools just test-domain hdmap
```

## Validate a Single File

A file **inside the repository** needs no extra setup — pass its repo-relative path:

```bash
docker compose run --rm ontology-tools \
    just validate-file tests/data/manifest/valid/manifest_instance.json
```

A file **outside the repository** is not visible to the container until you mount it. Add a
second bind mount and refer to the file by its path inside the container:

```bash
docker compose run --rm -v /absolute/path/to/my-data:/data:ro ontology-tools \
    just validate-file /data/my_manifest.json
```

`:ro` keeps the mount read-only, which is enough — validation only reads your data. Mount the
containing **directory**, not the file: `validate-file` scans the parent directory for
fixtures to resolve `did:web:` references from.

The exit code is the result, so this works in a script or CI step: `0` means the data
conforms and `210` is a conformance error, with the violations printed above it.

To validate several files, or a whole directory, use the underlying flag:

```bash
docker compose run --rm -v /absolute/path/to/my-data:/data:ro ontology-tools \
    just validate --data-paths /data/
```

## Things Worth Knowing

**Files the container writes are yours, not root's — if you built with your own ids.**
See [Build](#build) above: without `HOST_UID`/`HOST_GID` set to match your account, a
recipe that creates something new (rather than overwriting a file already there) leaves it
owned by uid/gid `1000` instead of you.

**The environment lives in a named volume, not in your working tree.** `UV_PROJECT_ENVIRONMENT`
points at `/opt/venv`, backed by a Docker volume, so a host `.venv` cannot shadow it — and a
host `.venv` built for a different platform cannot break the container.

**After a rebuild that changes dependencies — or `HOST_UID`/`HOST_GID` — reset that volume.**
Docker seeds a named volume from the image only while the volume is still empty, so an
existing volume keeps shadowing the new image, environment *and* ownership alike:

```bash
docker compose down -v && HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose build
```

**Submodules are bind-mounted, not baked in.** The image deliberately excludes
`submodules/` — around 300 MB that would only slow the build down. Tests that read the pinned
standards work because the bind mount carries them, so initialise them on the host as usual:

```bash
git submodule update --init --recursive
```

**`just lint` needs a real `.git` directory.** pre-commit does. If you work in a
`git worktree`, its `.git` is a *file* pointing outside the bind mount, where pre-commit
cannot follow it — run lint from a normal clone, or on the host.

**The image needs no network at run time.** Dependencies and the project are installed at
build time, so recipes work offline. `docker compose run --rm ontology-tools` with networking
disabled is a supported way to prove data validates against nothing but the pinned artifacts.
