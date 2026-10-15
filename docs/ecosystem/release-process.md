# Release Process

This guide describes how maintainers create a new release of the ontology repository.

## Prerequisites

Before creating a release, ensure:

- [ ] All PRs for the release are merged into `main`
- [ ] The version-bump PR is merged into `main`: `pyproject.toml`, `uv.lock` and the
      regenerated registry name the new version (see [Bumping the version](#bumping-the-version))
- [ ] Validation passes: `just test`
- [ ] Pre-commit hooks pass: `just lint`

## Creating a Release

### Option A — Tag Push (Recommended)

Create a signed, annotated tag and push it. The release workflow triggers automatically.

```bash
git checkout main
git pull origin main
git tag -a -s v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

This is the preferred method because:

- The tag is GPG-signed and annotated (matches repository signing policy).
- The tag exists before the workflow runs, so changelog generation resolves the correct commit range.
- The tag is immutable — it points to the exact commit you reviewed.

### Option B — Manual Workflow Dispatch

Use the GitHub Actions UI when you need to re-run a release or the tag already exists.

1. Go to **Actions** → **Release** → **Run workflow**.
2. Enter the release tag (e.g., `v0.2.0`).
3. Click **Run workflow**.

!!! warning "Tag must exist first"
    If the tag does not yet exist as a git tag, the workflow creates a lightweight
    tag at the current `main` HEAD. Prefer Option A to get a signed, annotated tag.

## What the Workflow Does

The [`cd-release.yml`](https://github.com/ASCS-eV/ontology-management-base/blob/main/.github/workflows/cd-release.yml) workflow runs these steps in order:

```mermaid
flowchart LR
    A[Update registry] --> B[Commit to main]
    B --> C[Generate changelog]
    C --> D[Create GitHub Release]
    D --> E[Build docs + W3ID artifacts]
```

| Step | Detail |
|------|--------|
| **Update registry** | Runs `registry_updater` with `--release-tag` to update `docs/registry.json` |
| **Commit to main** | Tries to push the registry update to `main`; the branch rules of `main` decline the push and the workflow continues. The version-bump PR has committed the registry already. |
| **Generate changelog** | Uses [git-cliff](https://git-cliff.org/) with `cliff.toml` to produce release notes from conventional commits |
| **Create GitHub Release** | Publishes the release on GitHub with the generated notes |
| **Build docs + W3ID** | Triggers `cd-docs.yml` to build documentation and versioned W3ID artifacts from the immutable tag |

### Publishing to PyPI

Publishing the package to [PyPI](https://pypi.org/p/ontology-management-base) is handled
by a separate workflow, [`cd-pypi.yml`](https://github.com/ASCS-eV/ontology-management-base/blob/main/.github/workflows/cd-pypi.yml),
which triggers when a GitHub Release is **published** (so it runs after `cd-release.yml`
creates the release). It builds the sdist and wheel, verifies the `pyproject.toml`
version matches the release tag, and uploads to PyPI using
[trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API tokens).

The publish step runs in the repository's `pypi` GitHub Actions environment, which must
exist in **Settings → Environments** (restricting it to release tags / protected refs is
recommended). No secrets are required; the `id-token: write` permission plus the
configured PyPI trusted publisher authorize the upload.

## Versioning

The repository uses [Semantic Versioning](https://semver.org/). While the version is
below `1.0.0`, the minor version takes the place of the major version, as is usual for
`0.y.z` releases: a release that breaks existing users raises the minor version, and
every other release raises the patch version. A dependency range such as
`>=0.5.1,<0.6` therefore receives fixes and additions but no breaking change, and a
breaking change in review can plan for the next minor version: releases made in the
meantime only raise the patch version.

The pull request template classifies each change; the release takes the largest bump
among its changes:

| Change (pull request classification) | Bump below `1.0.0` | Example | Bump from `1.0.0` |
|--------------------------------------|--------------------|---------|-------------------|
| Bug fix or non-breaking ontology correction (**Patch**) | Patch | `v0.5.0` → `v0.5.1` | Patch |
| Backward-compatible addition: a new domain or type, a new API or CLI feature (**Minor**) | Patch | `v0.5.0` → `v0.5.1` | Minor |
| Breaking change: existing Self-Descriptions become invalid, or a documented API or CLI changes incompatibly (**Major**) | Minor | `v0.5.1` → `v0.6.0` | Major |

### Bumping the version

The version-bump PR changes the version in `pyproject.toml`, the **single source of
truth** for the package version:

```toml
[project]
version = "0.5.1"
```

and commits what derives from it:

- `uv.lock` records the project's own version, and every `just` recipe runs
  `uv run --frozen`, which refuses a lock that disagrees with `pyproject.toml`. Change
  the `version` of the `ontology-management-base` package entry and check it with
  `uv lock --check`; `uv lock` would also re-resolve the git-pinned dependencies.
- `just registry-update` regenerates `docs/registry.json` (`latestRelease` and each
  ontology version's `releaseTag`) and `config/ontoenv.toml` for the new version. The
  documentation and the W3ID artifacts of a release are built from the registry at its
  tag, so the registry names the release before the tag is created.

`omb/__init__.py` reads `__version__` from the installed package metadata and needs no
change.

The release tag must match: for `version = "0.3.0"`, tag `v0.3.0`. The PyPI publish
workflow fails fast if the tag and `pyproject.toml` version disagree.

## Changelog Generation

Release notes are auto-generated from [Conventional Commits](https://www.conventionalcommits.org/) using [git-cliff](https://git-cliff.org/). Commit prefixes map to sections:

| Prefix | Section |
|--------|---------|
| `feat:` | Features |
| `fix:` | Bug Fixes |
| `docs:` | Documentation |
| `refactor:` | Refactoring |
| `test:` | Testing |
| `ci:` | CI/CD |
| `chore:` | Maintenance |

Configuration lives in [`cliff.toml`](https://github.com/ASCS-eV/ontology-management-base/blob/main/cliff.toml).

## Post-Release Verification

After the workflow completes, verify:

- [GitHub Release](https://github.com/ASCS-eV/ontology-management-base/releases) exists with correct notes
- `docs/registry.json` on `main` reflects the new tag
- [Documentation site](https://ascs-ev.github.io/ontology-management-base/) is updated
- W3ID IRIs resolve (e.g., `https://w3id.org/ascs-ev/envited-x/{domain}/v{n}`)
