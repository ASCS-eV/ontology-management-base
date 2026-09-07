# Development container for the Ontology Management Base.
#
# Gives a contributor the full toolchain — uv, just, the dev dependency group — without
# installing any of it on the host. This is a development environment, not a shipping
# artifact: the package is published as a wheel built from pyproject.toml, and nothing
# here takes part in that build.
#
#   docker compose build && docker compose run --rm ontology-tools
#   just --list
#
# compose.yaml bind-mounts the repository at /workspace, so host edits are visible
# immediately and generated artifacts land back in the working tree.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# justfile exports these for every recipe; setting them here means a bare `python` in the
# container behaves the same as one launched through `just`.
ENV PYTHONUTF8=1
ENV PYTHONIOENCODING=utf-8
# Point uv at a fixed environment path instead of an in-tree .venv, which the bind mount
# would otherwise shadow with whatever the host has.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# The environment is a named volume and uv's cache is an image layer, so they are always on
# different filesystems and hardlinking can never work. Say so, rather than let uv warn
# about it on every single run.
ENV UV_LINK_MODE=copy
# Installed system-wide (not a per-user ~/.local/bin) so both root, during this build, and
# the non-root user created below, at runtime, can run them. UV_TOOL_DIR matters as much as
# UV_TOOL_BIN_DIR: the bin dir only holds a shim, and without also relocating the tool's own
# venv, `uv tool install` (run below, as root) would store it under /root, which is 700 and
# unreadable to the user this image switches to further down — breaking the shim it just
# placed on PATH.
ENV UV_INSTALL_DIR=/usr/local/bin
ENV UV_TOOL_DIR=/usr/local/share/uv/tools
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace

# git is a runtime dependency, not just a build one: the validation suite and the
# submodule-backed tests invoke it. build-essential covers dev dependencies that still
# ship only an sdist.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# uv manages both the environment and Python; just runs the recipes. justfile requires
# both on PATH. Installing just through uv keeps it to a single installer.
RUN curl -fsSL https://astral.sh/uv/install.sh | sh \
    && uv tool install rust-just

# A recipe run in the container (e.g. `just docs-build`, or `mkdir -p artifacts/$domain`
# in `generate-domain`) writes into /workspace, which compose.yaml bind-mounts from the
# host — so whatever user owns that write decides who can read or delete it back on the
# host afterwards. Running as root, as this image did before, means every *new* file or
# directory a recipe creates comes back root-owned: unwritable, and even undeletable
# without sudo, for the host account that ran `docker compose`. Existing tracked files
# are unaffected (root can overwrite an existing inode without changing its ownership),
# which is why this only bites on `docs-build`'s `site/`, a fresh `generate-domain`
# directory, coverage's `htmlcov/`, and similar first-time writes.
#
# HOST_UID/HOST_GID default to 1000 (the common single-account Linux default). Override
# them at build time to match your own account exactly, so every file the container
# writes is already yours on the host:
#   HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose build
ARG HOST_UID=1000
ARG HOST_GID=1000
RUN groupadd --gid "${HOST_GID}" omb \
    && useradd --uid "${HOST_UID}" --gid "${HOST_GID}" --create-home --shell /bin/bash omb \
    # /opt is root:root; the venv directory has to exist and be writable by omb before
    # `uv sync`, running as omb from here on, can create the environment inside it.
    && mkdir -p /opt/venv \
    && chown "${HOST_UID}:${HOST_GID}" /opt/venv
ENV HOME=/home/omb
USER omb

# Dependency metadata only, so this layer is reused until the dependency graph changes.
# uv.lock is copied deliberately: the recipes run `uv run --frozen`, which requires the
# lock and refuses to re-resolve — and the dev group pins linkml from a git branch, whose
# resolution must not drift inside the image. --chown matches the copy's ownership to the
# user that runs every subsequent RUN, so the layer below has something it can write next
# to, and nothing here ends up root-owned either.
COPY --chown=omb:omb pyproject.toml uv.lock README.md ./

# Dependencies first, without the project: this is the expensive layer — it resolves the
# whole dev group, including linkml from a git branch — and it must not be invalidated by
# an artifact edit.
RUN uv sync --frozen --no-install-project --group dev

# The project installs itself, and its wheel force-includes artifacts/, imports/ and
# docs/registry.json (pyproject.toml [tool.hatch.build.targets.wheel.force-include]), so
# hatchling needs all of them present or the build fails on a missing forced include.
# They arrive after the dependency sync so that changing an artifact re-runs only the
# project install below, not the resolution above.
COPY --chown=omb:omb omb ./omb
COPY --chown=omb:omb artifacts ./artifacts
COPY --chown=omb:omb imports ./imports
COPY --chown=omb:omb docs/registry.json ./docs/registry.json

# Installs the project alone; the dependencies are already present. Doing it at build time
# rather than leaving it to the first `uv run` keeps the image self-contained: otherwise
# every `docker compose run --rm` would have to reach the network for the build backend.
# The bind mount shadows the copies above at run time, which is the intent — the image
# supplies the environment, the mount supplies the code being worked on.
RUN uv sync --frozen --group dev

CMD ["bash"]
