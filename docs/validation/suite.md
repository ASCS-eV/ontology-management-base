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

Use `--data-paths` to validate JSON-LD files. Every document in a requested directory
is input, including DID documents. Siblings of explicitly named files are available
for reference resolution only:

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

Record a snapshot from the live report with `--update-expected`. This also works for a
file that has **no** snapshot yet — that is how a fixture is created:

```bash
just validate --run check-failing-tests --data-paths ./my/case.json --update-expected
```

In a recording run every named file is a candidate fixture: those that fail get a
snapshot written, those that pass are reported as "not a negative fixture" and left as
ordinary data. A recording run producing no negative snapshots fails. Review the
recorded snapshot before committing it.

An explicit `--run check-failing-tests` over `--data-paths` that finds no negative
fixture at all exits non-zero and says so, rather than reporting success for a run that
verified nothing.

`tests/data/{domain}/{valid,invalid}/` remains this repository's filing convention and is
how fixtures are discovered, but it grants nothing: a fixture filed under `invalid/` with no
snapshot is ordinary data. `tests/unit/test_negative_fixture_pairing.py` fails if the filing
and the pairing ever disagree, so the convention stays honest without being load-bearing.

!!! note "A snapshot's validated-file line names the file, not its path"

    The report includes the list of files validated, but the `.expected` snapshot records
    only the bare filename there, not the directory it happened to sit in when recorded.
    Directory never carries meaning for the pairing above, so it carries none for the
    comparison either: moving a fixture and its snapshot together — to reorganise a
    directory, or to hand both to `--data-paths` from outside the repository — still
    matches. Renaming the file, or breaking the pairing, still does not.

## External Artifacts

Use `--artifacts` to register external artifact directories, so data typed with a
vocabulary OMB does not ship can find its shapes:

```bash
just validate --data-paths ./data.json --artifacts ../other-repo/artifacts
```

Each directory holds `{domain}/{domain}.owl.ttl` (plus `{domain}.shacl.ttl` and
`{domain}.context.jsonld`) — the layout `gen-owl`/`gen-shacl`/`gen-jsonld-context`
produce. A subdirectory without the `.owl.ttl` is reported and skipped.

!!! warning "A run that loads no shapes fails"

    SHACL calls an empty shapes graph conformant, so a forgotten or misspelled
    `--artifacts`, a half-generated artifacts directory, or an `@type` no catalog knows
    would otherwise print "Validation PASSED" having checked nothing. Both merged and
    per-resource validation require an active SHACL target in every input document;
    empty documents and untargeted inputs fail with `210`. Property shapes and implicit
    node shapes count too. See the [consumer contract](consumer-contract.md) for strict
    mode, reference resolution and coverage semantics.

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

