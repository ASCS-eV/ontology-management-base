# GX Version Management

This document explains how Gaia-X versions are tracked in this repository.

## Version Format

The `VERSION` file uses semantic-like versioning with post-release patches:

```
<upstream-version>[+fix.<N>]
```

Examples:
- `25.11` - Official 25.11 release label
- `25.11+fix.1` - Official 25.11 plus one additional fix commit
- `25.11+fix.2` - Official 25.11 plus two additional fix commits

The `VERSION` file is the Gaia-X release label used in OMB docs. Exact
`service-characteristics` provenance is stored separately in `UPSTREAM_REF`
and `UPSTREAM_COMMIT`.

## Current Version: 25.11+fix.2

### Base Version
- **Upstream Tag**: 25.11
- **Submodule URL**: https://gitlab.com/ascs-ev/service-characteristics
- **Tag Commit**: 3051644

### Post-Release Fixes

#### +fix.1: Double Hash Fragment Fix (c41d423)
- **Commit**: [c41d4230](https://gitlab.com/ascs-ev/service-characteristics/-/commit/c41d4230bded3b362cf57e7ff190eba59dd1078e)
- **Branch**: fix/envited-ontologies
- **Author**: Carlo van Driesten
- **Date**: 2026-02-06
- **Description**: Fixes enum IRI generation to avoid double hash fragments
- **Files Changed**: `merge_schemas.sh`
- **Reason**: Critical fix for OWL enum IRI generation that was causing invalid IRIs like `https://w3id.org/gaia-x/development##Value` instead of `https://w3id.org/gaia-x/development#/Value`

#### +fix.2: LinkML-Compatible schema.org Prefix Fix (711b6d4)
- **Commit**: [711b6d4](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics/-/commit/711b6d4aee19667f7c6ed8b3a33ab0444d3c4c68)
- **Branch**: fix/354-rename-httpsschema-prefix
- **Description**: Replaces the non-standard `httpsschema` prefix with `schema` and uses `http://schema.org/` to remain compatible with `linkml:types`
- **Reason**: Prevents LinkML prefix merge failures while keeping the generated Gaia-X artifacts aligned with the upstream build pipeline

### Why Post-Release Patches?

We use post-release patches when:

1. An upstream bug affects our use case
2. We contribute a fix but the next upstream release isn't available yet
3. We need the fix immediately for development/testing

Once the upstream releases a new version that includes these fixes, we update to that official release.

## Verification

Check if recorded upstream provenance matches the submodule:

```bash
./verify-version.sh
```

Expected output for synchronized post-release patches:
```
✓ Upstream metadata matches the checked-out submodule.
```

## Migration Path

When upstream releases 25.12 (or later) that includes these fixes:

1. Check out the new tag: `cd submodules/service-characteristics && git checkout 25.12`
2. Update artifacts: `./update-from-submodule.sh 25.12`
3. Update VERSION: `echo "25.12" > VERSION` (remove +fix suffix)
4. Refresh provenance files by running `make generate gx`
5. Update README.md to remove the "Post-release fixes" section
6. Regenerate docs and commit

## References

- [Submodule Repository](https://gitlab.com/ascs-ev/service-characteristics)
- [Fix Commit (+fix.1)](https://gitlab.com/ascs-ev/service-characteristics/-/commit/c41d4230bded3b362cf57e7ff190eba59dd1078e)
- [Fix Commit (+fix.2)](https://gitlab.com/gaia-x/technical-committee/service-characteristics-working-group/service-characteristics/-/commit/711b6d4aee19667f7c6ed8b3a33ab0444d3c4c68)
- [artifacts/gx/README.md](README.md) - General GX documentation
