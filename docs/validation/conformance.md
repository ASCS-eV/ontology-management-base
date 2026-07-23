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

## Behavior

- Resolves required schemas via catalogs
- Filters base ontologies by predicates, types, and datatypes
- Loads fixtures for `did:web:` references
- Applies RDFS inference before SHACL validation

