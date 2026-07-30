# Long-Term Maintenance

This is the active development home for ENVITED-X ontologies, maintained by [ASCS e.V.](https://www.asc-s.de/)

The repository was forked from [GAIA-X4PLC-AAD/ontology-management-base](https://github.com/GAIA-X4PLC-AAD/ontology-management-base), which was archived after release `v0.1.0`.

## Current Status

- **Active repository:** [ASCS-eV/ontology-management-base](https://github.com/ASCS-eV/ontology-management-base)
- **Documentation:** [ascs-ev.github.io/ontology-management-base](https://ascs-ev.github.io/ontology-management-base/)
- Issues and pull requests should be opened in this repository

## IRI Namespace Migration

Legacy ontologies use the `gaia-x4plcaad` W3ID namespace. When bumping a legacy ontology's version, its IRI is migrated to the `ascs-ev/envited-x` namespace with `owl:priorVersion` linking back to the old IRI. See [Discovery & Resolution](../discovery/index.md) for details.

## Tightening a Constraint: Deprecation Windows

The pull request template classifies a change as **Major** when it *"makes existing
Self-Descriptions invalid"*. That is a statement about validation outcomes, and a change to
SHACL shapes alone can trigger it while the OWL ontology — its classes and properties — stays
untouched. Bumping the version IRI in that situation is expensive: the version is part of the
namespace (`.../hdmap/v6/`), so every artifact, catalog entry, registry record and every
producer's `@context` has to move.

There is a second route, and the choice between them follows one question:

> **Was the constraint enforced before, or was it inert?**

- **It was enforced, and you want to tighten it further** — that is a genuine breaking change.
  Bump the ontology to `v{n+1}` with `owl:priorVersion`, per the namespace-migration policy
  above.
- **It was inert — declared but never actually applied** — then assets were accepted because
  of a defect, not because the model permitted them. Land the corrected constraint at
  `sh:severity sh:Warning` with a stated window, so existing self-descriptions keep
  validating while their authors get an actionable signal, and promote it to `sh:Violation`
  at the next version bump. Consumers then migrate once.

A deprecation window is **only** for the second case. Never relax a constraint that already
worked: that would newly accept data the model has always rejected, which is a silent
regression rather than a migration aid.

### How a window looks

Declare the affected constraints on their own node shape, because `sh:severity` applies to
every constraint of the shape that declares it:

```turtle
hdmap:OpenDriveRevisionAdvisoryShape a sh:NodeShape ;
    sh:targetClass hdmap:DomainSpecification ;
    sh:severity sh:Warning ;
    sh:message "... Accepted for now: this becomes an error in hdmap v7."@en ;
    sh:node hdmap:OpenDriveRoadTypeRevisionShape,
        hdmap:OpenDriveLaneTypeRevisionShape .
```

Warnings are reported by `just validate` in a separate **"Advisory results (do not fail
validation)"** section and never enter the recorded `.expected` snapshots, so a window can be
opened without churning unrelated negative tests.

Record in the shape's comment what the window is for and when it closes, and cover it with a
fixture under `tests/data/{domain}/valid/` that validates *and* produces the advisory — an
advisory nobody demonstrates is an advisory nobody notices.

### Worked example

`hdmap` v6 carries such a window. The OpenDRIVE revision checks introduced for #48 never
fired: each `sh:or` had a widest branch with no version guard, and that branch absorbed every
asset, so an OpenDRIVE 1.4 map could declare `laneTypes "walking"` — a value introduced in
v1.8 — and validate. Two fixtures in this repository did exactly that. The corrected
constraints for `roadTypes` and `laneTypes` are therefore warnings until `hdmap` v7.
`levelOfDetail` is **not** in the window: its check always worked, so it remains an error.

## Governance

The long-term governance of ENVITED-X ontologies is managed by ASCS e.V. to ensure continuity beyond the Gaia-X 4 PLC-AAD project phase.
