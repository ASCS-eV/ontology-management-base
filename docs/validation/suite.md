# Validation Suite

`validation_suite.py` is the orchestrator for all checks.

## Run All Checks

```bash
just validate --run all
```

## Run a Single Check

```bash
just validate --run check-data-conformance --domain hdmap
```

## Data Paths Mode

Use `--data-paths` to validate arbitrary files. Fixtures are auto-discovered from referenced IRIs:

```bash
just validate --data-paths path/to/data.jsonld
```

Multiple files or directories can be provided:

```bash
just validate --data-paths file1.json file2.json ./directory/
```

## External Artifacts

Use `--artifacts` to register external artifact directories (for schema resolution):

```bash
just validate --data-paths ./data.json --artifacts ../other-repo/artifacts
```

## Inference Mode

Control RDFS/OWL inference with `--inference-mode`:

```bash
just validate --domain hdmap --inference-mode owlrl
```

Options: `rdfs` (default), `owlrl`, `none`, `both`

## Check Types

- `check-syntax` — JSON/Turtle well-formedness
- `check-artifact-coherence` — SHACL targets exist in OWL (domain mode only)
- `check-data-conformance` — SHACL validation of instance data
- `check-failing-tests` — Invalid data fails as expected (domain mode only)
- `all` — Run all applicable checks

