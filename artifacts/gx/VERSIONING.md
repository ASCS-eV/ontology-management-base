# GX Version Management

This document explains how Gaia-X versions are tracked in this repository.

## Source of Truth

The `gx` artifacts are generated from the `service-characteristics` submodule,
which is pinned to the **canonical upstream Gaia-X repository**:

- **Submodule URL**: https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics
- **Submodule path**: `submodules/service-characteristics`

ASCS e.V. has write access upstream, so fixes are contributed directly to the
upstream project rather than carried on a fork. There is no downstream patch
queue to maintain.

## Version Format

`artifacts/gx/VERSION` is the Gaia-X release label used in OMB docs. It is
written automatically by `update-from-submodule.sh` from the submodule's git
state:

| Submodule state | `VERSION` format | Example |
| --- | --- | --- |
| On an exact release tag | leading `v` stripped, then truncated at the first `-` | `v2.5.0` → `2.5.0` |
| Ahead of a release tag | `<base>-ascs.<N>` | `2.5.0-ascs.3` |
| No reachable tag / unparsable `git describe` | previous `VERSION` is kept unchanged | — |

The `-ascs.<N>` form means "N commits beyond upstream tag `v<base>`" and only
appears when the submodule is deliberately pinned to an unreleased commit —
for example while a contributed fix is awaiting an upstream release.

> **Caution:** because the exact-tag branch truncates at the first `-`, a
> prerelease tag such as `v2.0.1-develop.13` yields `VERSION=2.0.1`, which is
> indistinguishable from the real `v2.0.1` release. `VERSION` propagates into
> `owl:versionInfo` and the generated docs paths, so pin to final release tags
> unless you have a specific reason not to. `UPSTREAM_REF` always records the
> unambiguous ref.

Exact provenance is always stored separately, regardless of format:

- `UPSTREAM_REF` — output of `git describe --tags --always --dirty`
  (e.g. `v2.5.0`, or `v2.5.0-dirty` for a modified submodule working tree)
- `UPSTREAM_COMMIT` — full submodule commit SHA

> **Caution:** `verify-version.sh` compares only `UPSTREAM_COMMIT` against
> `git rev-parse HEAD`. A submodule with uncommitted local modifications still
> verifies as matching, even though the generated artifacts do not correspond
> to the recorded commit. Check `UPSTREAM_REF` for a `-dirty` suffix.

`update-from-submodule.sh` also embeds `owl:versionInfo` and an `rdfs:comment`
into `gx.owl.ttl` so downstream consumers can identify the profile.

## Current Version: 2.5.0

- **Upstream Tag**: `v2.5.0`
- **Commit**: [6316558](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics/-/commit/6316558730e897de5945ab3eb1bce0455712240f)
- **Post-release fixes**: none — this is a clean upstream release

### Previously Carried Fixes (now upstream)

These fixes were maintained downstream on an ASCS fork prior to `v2.5.0` and
are included in the upstream release. They are listed for historical context
only; no action is required.

| Fix | Description | Status |
| --- | --- | --- |
| Double hash fragment (`c41d423`) | Fixed enum IRI generation producing `...development##Value` instead of `...development#/Value` | Upstream |
| schema.org prefix (`711b6d4`) | Replaced non-standard `httpsschema` prefix with `schema` / `https://schema.org/` for `linkml:types` compatibility | Upstream |

## Updating to a New Upstream Release

```bash
# 1. Ensure your local clone points at the canonical upstream
git submodule sync --recursive

# 2. Check out the new tag
cd submodules/service-characteristics
git fetch --tags origin
git checkout v2.6.0
cd ../..

# 3. Regenerate artifacts and provenance files
just generate-gx

# 4. Regenerate catalogs and docs
just registry-update
just docs-generate

# 5. Validate
just validate --domain gx
```

If the upstream release changes the schema, instance fixtures in
`tests/data/gx/` may need migrating, and `.expected` snapshots re-recorded
with `just validate --domain gx --update-expected`.

## Verification

Check that the recorded upstream provenance matches the submodule:

```bash
./verify-version.sh
```

Expected output:

```
✓ Upstream metadata matches the checked-out submodule.
```

## References

- [Upstream Repository](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics)
- [Upstream Release v2.5.0](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics/-/tree/v2.5.0)
- [artifacts/gx/README.md](README.md) - General GX documentation
