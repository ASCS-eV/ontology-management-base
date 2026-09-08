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

!!! note "No Docker license? Use Podman"

    Everything on this page works unchanged with [Podman](https://podman.io/) instead of
    Docker — useful where Docker Desktop's license doesn't apply (e.g. larger companies
    without a subscription). Verified end to end on Windows: `winget install RedHat.Podman`,
    then `pip install podman-compose` to give `podman compose` a Compose provider (Podman
    itself doesn't ship one). `podman machine init --now` creates the Linux VM Podman needs
    on Windows — it uses WSL2 the same way Docker Desktop does, so the same WSL2 prerequisite
    applies. From there, every command on this page is `podman compose` in place of
    `docker compose`, unchanged otherwise.

    On Windows specifically, `podman compose run --rm ontology-tools id` reports
    `uid=1000(omb)` regardless of `HOST_UID`/`HOST_GID` — but a file that recipe creates
    still lands on the NTFS side owned by your real Windows account, not root, because
    Windows enforces access through NTFS permissions on the account running Podman rather
    than the container's Linux-side uid (see the Windows note under Build).

!!! note "WSL2 without Docker Desktop"

    A third option, free of both Docker Desktop's license and Podman's extra
    `podman-compose` dependency: install Docker Engine directly inside your WSL2 distro
    (`sudo apt install docker.io docker-compose-v2`) instead of Docker Desktop. This is
    plain Docker CE — Docker Desktop is the piece that needs a license, not the engine —
    and everything on this page works unchanged from a WSL bash shell against it.

    Right after installing, `docker.service` can fail to start under `systemctl` on some
    WSL2 setups (`Job for docker.service canceled`) even though `dockerd` itself is fine —
    observed on a fresh install here. `wsl --shutdown` from PowerShell, then reopening the
    distro, resolves it in most cases by giving systemd a clean restart to pick up the
    newly installed units and the `docker` group. If it still doesn't start, run
    `sudo dockerd` in a spare terminal as a fallback — everything on this page works
    against it identically either way.

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

!!! note "Windows"

    `HOST_UID`/`HOST_GID` matching is a Linux/WSL2 concept — NTFS has no uid or gid to
    match in the first place. Whether it applies depends on *where the repository is
    cloned*, not on Windows itself:

    - **Cloned inside the WSL2 filesystem** (e.g. `\\wsl$\Ubuntu\home\you\...`, not
      `C:\...`), **built from a WSL bash shell** — WSL2 is a real Linux VM with real
      uid/gid semantics, so this works exactly as described above; use the same command.
    - **Cloned on the Windows filesystem** (`C:\...`, including as `/mnt/c/...` from
      WSL) — Docker Desktop bridges that bind mount over a protocol with no uid/gid of
      its own. Files the container writes typically show up owned by a fixed, synthetic
      identity no matter what `HOST_UID`/`HOST_GID` is set to, and `chown` inside the
      container does not persist. In practice this is usually *not* the blocking version
      of the problem described above, though: Windows enforces access through the NTFS
      permissions of the account running Docker Desktop, not the Linux-side uid, so
      Explorer/VS Code can typically still edit or delete those files regardless of what
      a `docker compose run --rm ontology-tools ls -la` reports.

    `$(id -u)`/`$(id -g)` are bash syntax; from PowerShell, set the same build args
    without them (the default matches the common single-account WSL2 case, uid/gid
    `1000`, so this is only needed if your WSL2 account's ids differ from that):

    ```powershell
    $env:HOST_UID = 1000
    $env:HOST_GID = 1000
    docker compose build
    ```

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
owned by uid/gid `1000` instead of you. On Windows this only applies at all when the
repository is cloned inside the WSL2 filesystem — see the Windows note under Build.

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
