# Long-Term Maintenance

This is the active development home for ENVITED-X ontologies, maintained by [ASCS e.V.](https://www.2simulations.de/)

The repository was forked from [GAIA-X4PLC-AAD/ontology-management-base](https://github.com/GAIA-X4PLC-AAD/ontology-management-base), which was archived after release `v0.1.0`.

## Current Status

- **Active repository:** [ASCS-eV/ontology-management-base](https://github.com/ASCS-eV/ontology-management-base)
- **Documentation:** [ascs-ev.github.io/ontology-management-base](https://ascs-ev.github.io/ontology-management-base/)
- Issues and pull requests should be opened in this repository

## IRI Namespace Migration

Legacy ontologies use the `gaia-x4plcaad` W3ID namespace. When bumping a legacy ontology's version, its IRI is migrated to the `ascs-ev/envited-x` namespace with `owl:priorVersion` linking back to the old IRI. See [W3ID resolution](../discovery/w3id-resolution.md) for details.

## Governance

The long-term governance of ENVITED-X ontologies is managed by ASCS e.V. to ensure continuity beyond the Gaia-X 4 PLC-AAD project phase.
