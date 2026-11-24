# Catalogs and Resolution

Validation tools resolve ontologies and shapes through XML catalogs.

## Catalogs

- `artifacts/catalog-v001.xml` maps domain IRIs to OWL, SHACL, and context files
- `imports/catalog-v001.xml` maps base vocabularies used for inference
- `tests/catalog-v001.xml` maps test data and fixtures

## Shared IRIs

Each catalog maps an IRI to one file. Several test-data files may describe the same node, since a self-contained file repeats the nodes it references; `tests/catalog-v001.xml` then maps the IRI to the file whose path sorts first and the generator logs the others. Fixtures follow the same rule, so the catalogs do not depend on the order in which the file system lists files.

## Resolver Behavior

`RegistryResolver` loads these catalogs and provides:

- `get_ontology_path(domain)`
- `get_shacl_paths(domain)`
- `get_context_path(domain)`
- `get_base_ontology_paths_for_iris(used_iris)`

## Why It Matters

Catalogs allow offline validation, deterministic file resolution, and consistent tooling across CI and local development.

