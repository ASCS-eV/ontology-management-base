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

### Negative Fixtures

A supplied file whose parent directory is named `invalid` is treated as a **negative
fixture**: it is expected to fail, and to fail with exactly the report recorded in the
`.expected` file beside it. `check-data-conformance` skips such files, and
`check-failing-tests` validates them instead — so passing one to `--run all` reports a
mismatch against its snapshot, not a pass:

```bash
just validate --data-paths tests/data/openlabel-v2/invalid/fail05_wrong_enum_value.json
```

If no `.expected` file exists beside the fixture the run fails, naming the file it wants.
Record the snapshot from the live report with:

```bash
just validate --run check-failing-tests --data-paths ./my/invalid/case.json --update-expected
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
- `check-failing-tests` — Invalid data fails as expected, and with the recorded output
- `all` — Run all applicable checks. Everything except `check-artifact-coherence`, which
  needs domain artifacts in the standard catalog layout.

