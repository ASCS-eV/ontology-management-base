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

A data file is a **negative fixture** — one expected to fail — if and only if a `.expected`
snapshot sits beside it, sharing its stem:

```
case.json       the data
case.expected   the report its failure must produce
```

That pairing is the whole rule. No directory name carries meaning, so a file validates the
same way wherever it lives. `check-data-conformance` leaves negative fixtures alone and
`check-failing-tests` compares each against its snapshot, and the output says so explicitly:

```
⏭️  Nothing to conformance-check in 'custom-path-6a6de4eb': all 1 file(s) are negative
    fixtures, verified by check-failing-tests against their snapshots.
      tests/data/openlabel-v2/invalid/fail05_wrong_enum_value.json  ←→  fail05_wrong_enum_value.expected

🔍 Negative fixture: tests/data/openlabel-v2/invalid/fail05_wrong_enum_value.json
   Paired snapshot: tests/data/openlabel-v2/invalid/fail05_wrong_enum_value.expected
   Validation returned 210 (conformance error), as recorded
✅ … failed as expected: its report matches …fail05_wrong_enum_value.expected, so the
   failure is accepted.
```

Everything else follows from the pairing:

| Situation | Result |
|---|---|
| Snapshot present, report matches | Failure accepted, exit `0` |
| Snapshot present, report differs | Exit `1` with a unified diff against the snapshot |
| Snapshot present, data no longer fails | Exit non-zero — the snapshot is stale, or the data was fixed and the snapshot should be deleted |
| No snapshot | Ordinary data: conformance-checked, real violations, exit `210` |

Record a snapshot from the live report with `--update-expected`:

```bash
just validate --run check-failing-tests --data-paths ./my/case.json --update-expected
```

`tests/data/{domain}/{valid,invalid}/` remains this repository's filing convention and is
how fixtures are discovered, but it grants nothing: a fixture filed under `invalid/` with no
snapshot is ordinary data. `tests/unit/test_negative_fixture_pairing.py` fails if the filing
and the pairing ever disagree, so the convention stays honest without being load-bearing.

!!! note "A snapshot records the path it was made from"

    The report includes the list of files validated, so a `.expected` file is tied to the
    path it was recorded at. Moving a fixture and its snapshot together still reports a
    mismatch on that line — re-record with `--update-expected` after moving.

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

