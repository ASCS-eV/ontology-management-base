# Tooling Index

This repository provides a small set of focused tools.

## Public API

- `omb.api` — the supported surface for other repositories: `validate_data`,
  `check_negative_fixtures`, `FixtureReport`/`FixtureOutcome`, plus
  `omb.core.result.ValidationResult` and `ReturnCodes`. See [Python API](python-api.md).
  Everything below is internal and may change in any release.

## Installed Commands

| Command | Module | Purpose |
|---|---|---|
| `onto-validate` | `validators/validation_suite.py` | Orchestrates all checks (also `python -m omb`) |
| `onto-check-conformance` | `validators/conformance_validator.py` | SHACL validation of instance data |
| `onto-check-coherence` | `validators/coherence_validator.py` | SHACL target classes against OWL |
| `onto-generate-docs` | `utils/properties_updater.py` | `PROPERTIES.md` and the docs property pages |
| `onto-generate-context` | `utils/context_generator.py` | `.context.jsonld` from OWL + SHACL |

Each returns its exit code, runs without a virtual environment, and forces UTF-8 output.

## Validators

- `validation_suite.py` orchestrates all checks
- `conformance_validator.py` runs SHACL validation
- `coherence_validator.py` checks SHACL target classes against OWL
- `syntax_validator.py` validates JSON-LD and Turtle syntax
- `shacl/` — the validation internals: `validator.py` (`ShaclValidator`),
  `schema_discovery.py` (type → schema routing), `inference.py` (RDFS/OWL)

## Registry and Catalog Tools

- `registry_updater.py` regenerates `docs/registry.json` and XML catalogs
- `registry_resolver.py` resolves domains and IRIs to file paths
- `file_collector.py` shared file discovery: catalog building, and the `--data-paths`
  top-level/fixture hierarchy
- `http_artifact_resolver.py` fetches and caches artifacts over HTTP (`--remote`)
- `context_resolver.py` resolves and inlines JSON-LD contexts
- `graph_loader.py` loads RDF graphs

## Generators

- `properties_updater.py` generates `artifacts/<domain>/PROPERTIES.md`,
  `docs/ontologies/properties/<domain>.md`, and the properties overview
- `class_page_generator.py` generates per-class documentation pages
- `context_generator.py` generates `.context.jsonld` files from OWL + SHACL
- `readme_updater.py` updates the README catalog table
- `asam_imports.py` derives the ASAM OpenDRIVE/OpenSCENARIO vocabularies from the
  standards submodule
- `xsd_enum_extractor.py` / `xsd_shacl_sync.py` keep `sh:in` enumerations in step with
  their pinned XSD sources

## Publishing Tools

Optional — installed with the `[publish]` extra, never imported by validation.

- `fc_upload_with_update.py` uploads OWL and SHACL files to the Gaia-X federated catalog
- `authhelper/keycloakhandling.py` obtains the tokens it needs
