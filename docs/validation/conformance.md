# SHACL Conformance

The conformance validator checks JSON-LD instances against SHACL shapes.

## Recommended Usage

```bash
just validate --run check-data-conformance --domain hdmap
```

## Direct Module Usage

```bash
python3 -m omb.validators.conformance_validator tests/data/hdmap/valid/
```

## From Another Repository

Data typed with a vocabulary OMB does not ship needs its artifacts registered, or there
are no shapes to validate against:

```bash
onto-check-conformance ./tests/data/valid --artifacts ./artifacts
```

The equivalent in Python is [`omb.api.validate_data`](python-api.md).

## Behavior

- Resolves required schemas via catalogs
- Filters base ontologies by predicates, types, and datatypes
- Loads fixtures for `did:web:` references
- Applies RDFS inference before SHACL validation
- **Fails when no SHACL shape was loaded for the data** — an empty shapes graph is
  conformant by definition, so reporting success there would mean "nothing was checked"
  and "everything passed" look identical

