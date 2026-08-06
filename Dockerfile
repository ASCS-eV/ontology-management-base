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
ENV PATH="/opt/venv/bin:/root/.local/bin:${PATH}"

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
    && /root/.local/bin/uv tool install rust-just

# Dependency metadata only, so this layer is reused until the dependency graph changes.
# uv.lock is copied deliberately: the recipes run `uv run --frozen`, which requires the
# lock and refuses to re-resolve — and the dev group pins linkml from a git branch, whose
# resolution must not drift inside the image.
COPY pyproject.toml uv.lock README.md ./

# The project installs itself, so the package must exist before sync. The bind mount
# shadows this copy at run time, which is the intent: the image supplies dependencies,
# the mount supplies the code being worked on.
COPY omb ./omb

RUN /root/.local/bin/uv sync --frozen --group dev

CMD ["bash"]
