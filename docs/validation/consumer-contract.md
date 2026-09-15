# Consumer contract

Install `ontology-management-base` from PyPI for the Python API and the five console
commands below. They work without a source checkout. The supported interfaces are
`omb.api` and its result types, the documented console commands, and `python -m omb`.
The Python modules implementing the commands are internal; importing those modules
is not a compatibility guarantee. Compatible additions may extend result types and
command options; removing or changing supported behavior requires a documented
migration. Correctness fixes can turn previously unchecked inputs into failures.

## Features and verification

| Feature | Supported interface | Inputs, effects and failures | Automated evidence |
|---|---|---|---|
| Positive validation | `omb.api.validate_data`, `onto-validate --run check-data-conformance`, `onto-check-conformance` | JSON-LD `.json`/`.jsonld` files or directories; bundled or caller artifacts; no data writes. No coverage, missing shapes and violations fail. | `test_missing_shapes_never_pass`, `test_every_input_needs_active_coverage`, `test_validation_commands_and_bundled_coherence` |
| Negative fixtures | `omb.api.check_negative_fixtures`, `onto-validate --run check-failing-tests` | Each data file with a same-stem `.expected` snapshot is verified. API checks and explicit CLI data-path checks fail when no fixture exists; changed reports and unexpected conformance fail. | `test_first_snapshots_and_mixed_did_snapshot_drift` |
| Snapshot recording | API `update=True`, CLI `--update-expected` | API and CLI data-path recording consider every requested data file. Writes snapshots for actual SHACL failures; refuses setup/coverage failures. These recording runs fail if no negative snapshot is written. Domain mode uses catalog fixtures. Review snapshot changes before committing. | `test_first_snapshots_and_mixed_did_snapshot_drift`, `test_negative_fixture_errors_are_reported_without_recording` |
| Syntax | `onto-validate --run check-syntax` | Checks JSON/Turtle syntax, without asserting data conformance. In data-paths mode inputs are JSON-LD files. Domain mode also checks catalog artifacts. | `test_syntax_cli_rejects_malformed_json`, source syntax unit tests |
| OWL/SHACL coherence | `onto-check-coherence DOMAIN [--root ROOT]`, suite `--run check-artifact-coherence --domain DOMAIN` | Checks shape target classes against OWL using catalogs. `--root` selects a complete catalog root. Data-paths `--run all` does not run coherence. | `test_validation_commands_and_bundled_coherence`, source coherence unit tests |
| Documentation generation | `onto-generate-docs --artifacts DIR --output DIR` | Writes caller-owned documentation; creates missing consumer catalog pages. See [generator paths](generators.md). | `test_generators_write_to_caller_output`, generator unit tests |
| JSON-LD context generation | `onto-generate-context --all --artifacts DIR --output DIR` | Writes contexts to caller output; malformed/missing input fails. See [generator paths](generators.md). | `test_generators_write_to_caller_output`, generator unit tests |
| Publishing dependencies | `pip install 'ontology-management-base[publish]'` | Optional requests/Keycloak integration; uploader/authhelper Python modules and their remote service protocol remain internal. Installing the extra does not publish anything. | `test_installed_boundary_and_optional_dependency_contract`; uploader unit tests stub remote services |
| Contributor toolchain | Docker Compose development container and `just` recipes | Requires a clone and bind mount; outputs belong to the caller. It is a development environment, not a distributed runtime image. | Docker build, ownership check, `just test-domain manifest`, `just test-contract` |

All named consumer tests live in `tests/contract/test_consumer_contract.py`. CI builds
both distributions, copies these tests outside the checkout, and runs them against a
fresh installation with no source import path. The wheel is tested with runtime
requirements only plus pytest, the sdist with `[publish]`, and the wheel again with the
minimum declared runtime dependency versions. Publication runs the same checks before
uploading. Ubuntu and Windows exercise the installed boundary; the source test matrix
also includes macOS. Container CI exercises the same contract against its development
environment. Remote publishing transactions are tested with stubs, not live credentials.

Run locally:

```bash
just test-contract
python scripts/verify_wheel_install.py --wheel 'dist/*.whl'
python scripts/verify_wheel_install.py --sdist 'dist/*.tar.gz' --publish
python scripts/verify_wheel_install.py --wheel 'dist/*.whl' --minimum
```

## Discovery and conformance

Every JSON-LD document inside a requested directory is input, including documents
with `did:` identifiers. Explicit files select only those files. Their siblings are
available for reference resolution but are not additional validation inputs. Missing
requested paths fail. Negative fixtures are excluded only from positive validation;
the full suite checks their snapshots. Use separate directories when reference-only
support documents must not receive their own validation verdict.

By default, positive inputs are merged into one RDF graph, including resolved reference
documents. Use `per_resource=True` / `--per-resource` to validate each requested file in
isolation without merging referenced documents. Both modes require each input file to
contribute at least one RDF term targeted by an active shape. Empty documents and files
with no applicable target fail with 210. Targets and inferred classes follow pySHACL;
property shapes and implicitly declared node shapes are supported.

This coverage check does **not** mean that every RDF triple or property is constrained.
The supplied shapes define that policy (for example, `sh:closed` rejects extra
properties). `shapes_loaded` counts discovered node and property shapes; it is diagnostic
metadata, not sufficient proof of coverage. In per-resource mode `report_graph` is
`None`; `report_text`, errors and routing metadata aggregate the individual verdicts.

## Defaults, network access and exit codes

- Python `validate_data` defaults to `strict=True`; the CLI defaults to `False`.
  Add `--strict` when translating that Python call. Strict mode rejects unresolved
  type IRIs in both merged and per-resource validation. Merged validation also rejects
  unresolved external instance references; per-resource validation does not load them.
- Inference defaults to `rdfs`; `none`, `owlrl` and `both` are also supported.
- CLI warnings/info are advisory unless `--fail-on-warnings` is set. The negative
  fixture API exposes `allow_warnings`; positive API validation uses advisory warnings.
- Python instance-reference resolution defaults to `allow_online=False`. The suite
  enables it unless `--offline` is supplied. `enable_http=True` / `--remote` separately
  opts into bootstrapping missing OMB artifacts over HTTP. These controls do not block
  RDFLib fetching an unmapped remote JSON-LD `@context`: register local contexts under
  `artifacts` when operating without network access.
- Validation returns 0 on success, 210 for conformance/coverage failures and 1 for
  input/setup errors. API positive validation returns `SKIPPED` (100, `conforms=False`)
  for an entirely negative-fixture input. A suite conformance phase can skip these
  fixtures; use `--run all` to verify their snapshots as well.
- Negative API reports use `ok` as the verdict and `return_code` 0/210. Inspect both
  `errors` and `failures` for diagnostics. CLI snapshot mismatch/no fixtures returns 1.
  Domain checks can skip domains without negative fixtures. CLI syntax checks return
  101 for malformed JSON and 102 for malformed Turtle; argument errors return 2.
  Generator failures return nonzero.
- Validation does not write input files; explicit recording and generation do.
  The API does not configure process logging or print. Host handlers can receive
  `omb.*` log records. Console output uses UTF-8; automate using exit codes and Python
  result fields rather than parsing decorative console reports.
