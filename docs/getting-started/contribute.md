# Contribute

This guide describes how to add or update ontologies, shapes, and test data.

## Workflow

1. Change the domain's source:
    - a generated domain (see [LinkML Models](../future/linkml.md)): its schema
      `linkml/{domain}/{domain}.yaml`, then run `just generate-domain {domain}`;
    - a hand-written domain: its OWL ontology, SHACL shapes and JSON-LD context
      under `artifacts/{domain}/`.
2. Add test instances under `tests/data/{domain}/`.
3. Update catalogs and registry.
4. Run validation.

## Catalog and Registry Updates

Run the updater to regenerate `docs/registry.json` and the XML catalogs:

```bash
just registry-update
```

This updates:

- `docs/registry.json`
- `artifacts/catalog-v001.xml`
- `imports/catalog-v001.xml`
- `tests/catalog-v001.xml`
- `config/ontoenv.toml`

The pre-commit hooks run this updater, and `properties_updater` for
`docs/ontologies/catalog.md` and `docs/ontologies/properties.md`, when an artifact
changes. Commit their output with the change: the documentation site is built from
the committed registry.

## Validation

```bash
just validate --run all --domain {domain}
```

## Documentation

Build or preview docs locally (auto-generates docs assets):

```bash
DOCS_SITE_URL=http://127.0.0.1:8000/ontology-management-base mkdocs serve
```

Notes:

Hook flow (via `hooks/copy_artifacts.py`):

1. The hook runs `properties_updater` and `class_page_generator` (DOCS_SITE_URL is optional and only affects local diagram links).
2. `properties_updater` writes tracked `artifacts/<domain>/PROPERTIES.md`, generates `docs/ontologies/properties/<domain>.md` (ignored by git), builds the `docs/ontologies/properties.md` domains overview, and refreshes `docs/ontologies/catalog.md`.
3. `class_page_generator` writes `docs/ontologies/classes/<domain>/*.md` and uses `DOCS_SITE_URL` to build local diagram links.
4. The hook copies `artifacts/<domain>/` into `docs/artifacts/<domain>/<versionInfo>/` and adds example instances from `tests/data/`.
5. Generated folders (`docs/artifacts/`, `docs/ontologies/classes/`, `docs/ontologies/properties/`) are ignored by git.

## Releasing

See the [Release Process](../ecosystem/release-process.md) guide for how maintainers
create tagged releases and publish documentation.

## Review Checklist

- Ontology IRI and version are consistent
- A generated domain is changed in its LinkML schema; its artifacts are the
  output of `just generate`
- SHACL shapes import the ontology
- Context points to the correct W3ID namespace
- Tests cover both valid and invalid cases
- Catalogs and registry are up to date
