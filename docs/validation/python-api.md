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
| must conform | `validate_data` | every input contributes an active SHACL target and the merged graph conforms |
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
| `shapes_loaded` | number of discovered node/property shapes, including implicit shapes |
| `types_routed` / `types_unrouted` | which `@type` IRIs found a schema |
| `per_type_shape_count` | shapes targeting each found type |
| `violations` | one `Violation` per distinct SHACL constraint violation, sorted |
| `errors` | why no verdict was reached: no input, no covering shape, strict-mode unresolved IRIs, a missing dependency |
| `warnings` | advisory notes, including skipped negative fixtures |

A failure states its reason in `violations` when the data broke a constraint, and in
`errors` when no verdict could be reached. A per-resource result aggregating several
files can carry both.

Each `Violation` (from `omb.core.result`) locates one failed constraint:

| Field | Meaning |
|---|---|
| `file` | the input file the violation was found in, as in `files_validated` |
| `path` | property path from `focus_node` to the failing value, e.g. `hasDomainSpecification/hasQuantity/numberTrafficObjects` |
| `message` | the constraint's message, with long node renderings shortened to `[ ... ]` |
| `component` | the SHACL constraint component, e.g. `MinCountConstraintComponent` |
| `focus_node` | where `path` starts: normally the document's subject IRI; a blank node reads `[BNODE]` |
| `value` | the offending value; empty for a missing property |
| `source_shape` | IRI of the shape declaring the constraint; empty for a blank-node shape |
| `severity` | `Violation`; `Warning` or `Info` only where warnings are configured to fail validation |

`str(violation)` reads `file: message (at path)`:

```python
for violation in result.violations:
    print(violation)
```

Only results that count against conformance appear. A violation inside a nested
shape is reported once, at the path rooted at the validated document, and blank node
identifiers are scrubbed, so the list is stable from run to run.

## Validating many documents one at a time

`validate_data` is stateless: every call builds a resolver, discovers the schemas and
parses the shapes graph. That is right for a single validation, but a caller that
validates documents **individually** — an API server, or a suite that needs to attribute
each violation to its own document — pays that setup on every call.

`ValidationSession` keeps the parsed schemas alive between calls:

```python
from omb.api import ValidationSession

session = ValidationSession(artifacts=["artifacts"])

for document in documents:
    result = session.validate([document])
    print(document, result.conforms)
```

The constructor takes everything that decides *which* schemas load (`artifacts`,
`inference_mode`, `strict`, `allow_online`, `enable_http`, `root_dir`); only the data —
and `per_resource` — varies per call. `session.validate(...)` returns exactly what the
equivalent `validate_data(...)` returns, including the vacuity guard.

`artifacts` and `root_dir` are resolved to absolute paths when the session is built, so a
relative path keeps meaning what it meant at construction even if the process later
changes its working directory.

Call `session.clear_cache()` if any schema source changes on disk mid-session; otherwise
the session keeps validating against the shapes as they were first read.

### Memory

Each distinct schema footprint the session sees retains fully parsed graphs. A service
validating untrusted documents meets a new footprint for every unrecognised `@type`, so
the cache is bounded — `max_cached_schemas` (default 8), oldest entry dropped first:

```python
session = ValidationSession(artifacts=["artifacts"], max_cached_schemas=32)
```

Raise it when you legitimately validate many different vocabularies and want them all
resident; lower it when memory matters more than reuse.

### What it does and does not speed up

It caches **schema loading only**. Each call still builds a fresh resolver — so fixture
mappings registered while validating one document can never resolve an IRI in the next —
and still runs inference and SHACL over that document.

On a large ontology, schema loading is the minority of a call: RDFS inference dominates,
because the merged path derives the closure over data **plus** ontology every time. Expect
a useful but modest improvement, not an order of magnitude.

If your documents do not need individual verdicts, prefer passing them to a **single**
call — `validate_data` accepts a sequence, and one call means one inference pass:

```python
result = validate_data(documents, artifacts=["artifacts"])   # one pass, not len(documents)
```

!!! note "Thread safety"
    A session is not thread-safe. Use one per thread, or guard calls with a lock.

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
A recording run that produces no negative snapshot fails.

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
    assert report.ok, "\n".join(report.errors + [f.message for f in report.failures])
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
`omb.core.result.ValidationResult`, `Violation` and `ReturnCodes` are the supported
surface.
The five documented console commands and `python -m omb` are supported too.
Resolvers, loaders, validator classes and CLI implementation modules are internal.
See the [consumer contract](consumer-contract.md) for defaults, failure modes, input
discovery and the feature-to-test matrix.

## Equivalent CLI

Everything above is also available from the command line — see
[Validation Suite](suite.md):

```bash
onto-validate --run check-data-conformance --data-paths tests/data/valid --artifacts artifacts --strict --offline
onto-validate --run check-failing-tests   --data-paths tests/data/invalid --artifacts artifacts --offline
onto-validate --run check-failing-tests   --data-paths tests/data/invalid --artifacts artifacts --offline --update-expected
```

The CLI's exit code is the return code (`0`, `210`, …), so it drops straight into CI.
