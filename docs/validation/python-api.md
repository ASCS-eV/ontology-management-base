# Python API

`omb.api` is the supported surface for other repositories — typically one that models
its data in LinkML, generates OWL/SHACL/JSON-LD artifacts, and wants its test suite to
prove that the generated shapes accept what they should and reject what they should not.

## Install

```bash
pip install ontology-management-base     # or: uv add ontology-management-base
```

The wheel carries OMB's own `artifacts/`, `imports/` and `docs/registry.json` inside the
package, so nothing needs a source checkout. Runtime dependencies are `rdflib`,
`pyshacl` and `oxrdflib` — the Gaia-X publishing stack lives in the optional
`[publish]` extra and is never imported by the validation path.

## Two functions, one rule

Data splits in two, and the split is what makes a green test run mean something:

| Your data | Function | Passes when |
|---|---|---|
| must conform | `validate_data` | every file validated cleanly against at least one shape |
| must fail (negative fixture) | `check_negative_fixtures` | every fixture failed in the way its `.expected` snapshot records |

A data file is a **negative fixture** if and only if a `.expected` snapshot sits beside
it, sharing its stem (`case.json` ←→ `case.expected`). No directory name carries
meaning. `validate_data` skips such files — and, if they are all you passed it, returns
a failure rather than a vacuous success, because a run that checked nothing must never
look like one that checked everything.

## Validate data that must conform

```python
from omb.api import validate_data

result = validate_data(
    ["tests/data/valid"],
    artifacts=["artifacts"],      # your generated artifacts
)

assert result.conforms, result.report_text
print(result.shapes_loaded, "shapes,", len(result.files_validated), "files")
```

`artifacts` points at directories laid out as `{domain}/{domain}.owl.ttl` (plus
`{domain}.shacl.ttl` and `{domain}.context.jsonld`) — exactly what `gen-owl`,
`gen-shacl` and `gen-jsonld-context` produce. **Without it, data using your own
vocabulary has no shapes to validate against**, and the result is a failure saying so:

```
No SHACL shapes were loaded, so nothing could be validated (unresolved @type IRI(s):
https://example.org/widget/v1/Widget). Register the artifacts that define these types …
```

Useful fields on the returned `ValidationResult`:

| Field | Meaning |
|---|---|
| `conforms` | the verdict |
| `return_code` | 0, `210` conformance error, `100` skipped |
| `report_text` | the formatted report |
| `shapes_loaded` | how many `sh:NodeShape`s were in play — `0` is always a failure |
| `types_routed` / `types_unrouted` | which `@type` IRIs found a schema |
| `per_type_shape_count` | shapes targeting each found type |
| `warnings` | advisory notes, including skipped negative fixtures |

## Check data that must fail

```python
from omb.api import check_negative_fixtures

report = check_negative_fixtures(["tests/data/invalid"], artifacts=["artifacts"])

assert report.ok, "\n".join(f"{f.message}\n{f.diff}" for f in report.failures)
```

`report.ok` is False when a fixture stopped failing, when it failed *differently* than
recorded (`failure.diff` shows how), and when no fixture was found at all.

### Recording a snapshot

A new fixture has no snapshot yet, so pass `update=True` once and review the diff before
committing:

```python
check_negative_fixtures(["tests/data/invalid/fail01_missing_serial.json"],
                        artifacts=["artifacts"], update=True)
```

In a recording run every named file is a candidate: those that fail get a snapshot
written, those that pass are reported as "not a negative fixture" and left alone.

## In a pytest suite

```python
import pytest
from omb.api import check_negative_fixtures, validate_data

ARTIFACTS = ["artifacts"]

def test_valid_instances_conform():
    result = validate_data(["tests/data/valid"], artifacts=ARTIFACTS)
    assert result.conforms, result.report_text
    assert result.shapes_loaded > 0          # belt and braces: nothing was vacuous

def test_invalid_instances_still_fail_as_recorded():
    report = check_negative_fixtures(["tests/data/invalid"], artifacts=ARTIFACTS)
    assert report.ok, "\n".join(f.message for f in report.failures)
```

## Logging and output

Nothing in `omb.api` writes to stdout or stderr, and importing OMB does not configure
logging. OMB's loggers live under the `omb` name:

```python
import logging
logging.getLogger("omb").setLevel(logging.ERROR)     # quiet
logging.getLogger("omb").addHandler(my_handler)      # or route it yourself
```

## Stability

`omb.api` (its functions, `FixtureReport`, `FixtureOutcome`) plus
`omb.core.result.ValidationResult` and `ReturnCodes` are the supported surface.
Resolvers, loaders, validator classes and the CLI modules are internal and may change
in any release.

## Equivalent CLI

Everything above is also available from the command line — see
[Validation Suite](suite.md):

```bash
onto-validate --run check-data-conformance --data-paths tests/data/valid --artifacts artifacts
onto-validate --run check-failing-tests   --data-paths tests/data/invalid --artifacts artifacts
onto-validate --run check-failing-tests   --data-paths tests/data/invalid --artifacts artifacts --update-expected
```

The CLI's exit code is the return code (`0`, `210`, …), so it drops straight into CI.
