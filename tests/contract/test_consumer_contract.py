"""Consumer contract, runnable from a copied directory against an installed wheel.

FEATURE SET:
============
Positive/negative validation, CLI parity, SHACL coverage and generator I/O.

USAGE:
======
pytest tests/contract; scripts/verify_wheel_install.py runs installed variants.

NOTES:
======
Fixtures are self-contained and never read the repository's tests/data directory.
"""

import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from omb.api import check_negative_fixtures, validate_data

NS = "https://example.org/widget/v1/"
OWL = f"""@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix w: <{NS}> .
w: a owl:Ontology . w:Widget a owl:Class .
w:SpecialWidget a owl:Class; rdfs:subClassOf w:Widget .
"""
SHAPES = f"""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix w: <{NS}> .
w:Shape a sh:NodeShape; sh:targetClass w:Widget;
sh:property [sh:path w:serial; sh:minCount 1; sh:message "Serial required"] .
"""


@pytest.fixture
def consumer(tmp_path):
    artifacts = tmp_path / "artifacts" / "widget"
    artifacts.mkdir(parents=True)
    (artifacts / "widget.owl.ttl").write_text(OWL, encoding="utf-8")
    (artifacts / "widget.shacl.ttl").write_text(SHAPES, encoding="utf-8")
    (artifacts / "widget.context.jsonld").write_text(
        json.dumps({"@context": {"@vocab": NS}}), encoding="utf-8"
    )
    return tmp_path


def write_data(root, name="item", *, valid=True, kind="Widget", identifier=None):
    path = root / "data" / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    data = {
        "@context": {"@vocab": NS},
        "@id": identifier or f"urn:item:{name}",
        "@type": kind,
    }
    if valid:
        data["serial"] = "123"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def run_cli(root, command, *args):
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONDONTWRITEBYTECODE="1")
    if os.environ.get("OMB_EXPECT_INSTALLED"):
        env.pop("PYTHONPATH", None)
        executable = Path(sys.executable).parent / (
            command + (".exe" if os.name == "nt" else "")
        )
        invocation = [str(executable)]
    else:
        # Exercise the declared entry point in source runs; installed runs above
        # invoke the actual console script in an unrelated working directory.
        entry = next(
            e
            for e in importlib.metadata.distribution(
                "ontology-management-base"
            ).entry_points
            if e.name == command
        )
        invocation = [
            sys.executable,
            "-c",
            f"import sys; from {entry.module} import {entry.attr}; sys.exit({entry.attr}())",
        ]
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    return subprocess.run(
        invocation + list(map(str, args)),
        cwd=root,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=90,
    )


@pytest.mark.parametrize("per_resource", [False, True])
@pytest.mark.parametrize("strict", [False, True])
def test_missing_shapes_never_pass(consumer, per_resource, strict):
    result = validate_data(
        [write_data(consumer)], per_resource=per_resource, strict=strict
    )
    assert not result.conforms and result.return_code == 210
    assert result.shapes_loaded == 0


@pytest.mark.parametrize("per_resource", [False, True])
def test_strict_routing_checks_every_input(consumer, per_resource):
    good = write_data(consumer, "good")
    bad = write_data(consumer, "bad", kind="https://unknown.example/Unmapped")
    result = validate_data(
        [good, bad], artifacts=[consumer / "artifacts"], per_resource=per_resource
    )
    assert not result.conforms and result.return_code == 210
    assert "https://unknown.example/Unmapped" in result.types_unrouted


@pytest.mark.parametrize("per_resource", [False, True])
@pytest.mark.parametrize("case", ["empty", "untargeted", "deactivated"])
def test_every_input_needs_active_coverage(consumer, per_resource, case):
    good = write_data(consumer, "good")
    bad = write_data(consumer, "bad", valid=False, kind="Widgte")
    if case == "empty":
        bad.write_text("{}", encoding="utf-8")
    if case == "deactivated":
        shapes = consumer / "artifacts/widget/widget.shacl.ttl"
        shapes.write_text(
            SHAPES.replace("a sh:NodeShape;", "a sh:NodeShape; sh:deactivated true;"),
            encoding="utf-8",
        )
    result = validate_data(
        [good, bad], artifacts=[consumer / "artifacts"], per_resource=per_resource
    )
    assert not result.conforms and result.return_code == 210
    assert result.errors
    assert "bad.json" in result.report_text


@pytest.mark.parametrize("per_resource", [False, True])
@pytest.mark.parametrize("shape", ["property", "implicit", "subject", "object", "node"])
def test_supported_shacl_targets_accept_and_reject(consumer, per_resource, shape):
    body = {
        "property": "w:S a sh:PropertyShape; sh:targetClass w:Widget; sh:path w:serial; sh:minCount 1 .",
        "implicit": "w:S sh:targetClass w:Widget; sh:property [sh:path w:serial; sh:minCount 1] .",
        "subject": 'w:S sh:targetSubjectsOf w:serial; sh:property [sh:path w:serial; sh:hasValue "123"] .',
        "object": 'w:S sh:targetObjectsOf w:serial; sh:in ("123") .',
        "node": "w:S sh:targetNode <urn:item:item>; sh:property [sh:path w:serial; sh:minCount 1] .",
    }[shape]
    (consumer / "artifacts/widget/widget.shacl.ttl").write_text(
        f"@prefix sh: <http://www.w3.org/ns/shacl#> . @prefix w: <{NS}> . {body}",
        encoding="utf-8",
    )
    data = write_data(consumer)
    result = validate_data(
        [data], artifacts=[consumer / "artifacts"], per_resource=per_resource
    )
    assert result.conforms, result.report_text
    assert result.shapes_loaded > 0
    payload = json.loads(data.read_text(encoding="utf-8"))
    if shape in {"subject", "object"}:
        payload["serial"] = "wrong"
    else:
        payload.pop("serial")
    data.write_text(json.dumps(payload), encoding="utf-8")
    result = validate_data(
        [data], artifacts=[consumer / "artifacts"], per_resource=per_resource
    )
    assert not result.conforms and result.return_code == 210
    assert not result.errors  # a real constraint violation, not a coverage failure
    if not per_resource:
        assert result.report_graph is not None


@pytest.mark.parametrize("mode", ["none", "rdfs", "owlrl", "both"])
@pytest.mark.parametrize("per_resource", [False, True])
def test_subclass_target_coverage(consumer, mode, per_resource):
    data = write_data(consumer, kind="SpecialWidget")
    result = validate_data(
        [data],
        artifacts=[consumer / "artifacts"],
        inference_mode=mode,
        per_resource=per_resource,
    )
    assert result.conforms, result.report_text


def test_directory_did_inputs_are_all_checked(consumer):
    paired = write_data(
        consumer, "paired", valid=False, identifier="did:example:paired"
    )
    bad = write_data(
        consumer, "unpaired", valid=False, identifier="did:example:unpaired"
    )
    artifacts = consumer / "artifacts"
    assert check_negative_fixtures([paired], artifacts=[artifacts], update=True).ok
    result = run_cli(
        consumer,
        "onto-validate",
        "--run",
        "all",
        "--data-paths",
        paired.parent,
        "--artifacts",
        artifacts,
        "--offline",
    )
    assert result.returncode == 210, result.stdout + result.stderr
    assert bad.name in result.stdout
    assert not validate_data([paired.parent], artifacts=[artifacts]).conforms


@pytest.mark.parametrize("all_did", [False, True])
def test_first_snapshots_and_mixed_did_snapshot_drift(consumer, all_did):
    first = write_data(
        consumer,
        "first",
        valid=False,
        identifier="did:example:first" if all_did else None,
    )
    second = write_data(
        consumer, "second", valid=False, identifier="did:example:second"
    )
    artifacts = consumer / "artifacts"
    args = [
        "--run",
        "check-failing-tests",
        "--data-paths",
        first.parent,
        "--artifacts",
        artifacts,
        "--offline",
    ]
    recorded = run_cli(consumer, "onto-validate", *args, "--update-expected")
    assert recorded.returncode == 0, recorded.stdout + recorded.stderr
    assert first.with_suffix(".expected").is_file()
    assert second.with_suffix(".expected").is_file()
    assert check_negative_fixtures([first.parent], artifacts=[artifacts]).ok
    second.with_suffix(".expected").write_text("stale", encoding="utf-8")
    assert run_cli(consumer, "onto-validate", *args).returncode != 0
    assert not check_negative_fixtures([first.parent], artifacts=[artifacts]).ok


def test_per_resource_did_directory_and_explicit_sibling_boundary(consumer):
    good = write_data(consumer, identifier="did:example:good")
    assert validate_data(
        [good.parent], artifacts=[consumer / "artifacts"], per_resource=True
    ).conforms
    write_data(consumer, "bad", valid=False)
    result = validate_data(
        [good], artifacts=[consumer / "artifacts"], per_resource=True
    )
    assert result.conforms and len(result.files_validated) == 1


@pytest.mark.parametrize(
    "command",
    [
        "onto-validate",
        "onto-check-conformance",
        "onto-check-coherence",
        "onto-generate-docs",
        "onto-generate-context",
    ],
)
def test_installed_help(consumer, command):
    result = run_cli(consumer, command, "--help")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout


def test_validation_commands_and_bundled_coherence(consumer):
    data = write_data(consumer)
    for command, args in [
        (
            "onto-validate",
            ["--run", "check-data-conformance", "--data-paths", data, "--offline"],
        ),
        ("onto-check-conformance", [data]),
    ]:
        result = run_cli(
            consumer, command, *args, "--artifacts", consumer / "artifacts"
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert run_cli(consumer, command, *args).returncode == 210
    result = run_cli(consumer, "onto-check-coherence", "manifest")
    assert result.returncode == 0, result.stdout + result.stderr


def test_generators_write_to_caller_output(consumer):
    import omb

    package = Path(omb.__file__).parent

    def fingerprint():
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in package.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }

    before = fingerprint()
    for command, output, expected in [
        ("onto-generate-context", "contexts", "widget/widget.context.jsonld"),
        ("onto-generate-docs", "documentation", "artifacts/widget/PROPERTIES.md"),
    ]:
        args = ["--artifacts", consumer / "artifacts", "--output", consumer / output]
        if command.endswith("context"):
            args += ["--all"]
        result = run_cli(consumer, command, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (consumer / output / expected).is_file()
        bad = run_cli(
            consumer,
            command,
            "--artifacts",
            consumer / "missing",
            "--output",
            consumer / output,
        )
        assert bad.returncode != 0
    if os.environ.get("OMB_EXPECT_INSTALLED"):
        for command, args, expected in [
            (
                "onto-generate-context",
                ["--domain", "manifest"],
                "generated-contexts/manifest/manifest.context.jsonld",
            ),
            ("onto-generate-docs", [], "generated-docs/docs/ontologies/catalog.md"),
        ]:
            result = run_cli(consumer, command, *args)
            assert result.returncode == 0, result.stdout + result.stderr
            assert (consumer / expected).is_file()
            forbidden = run_cli(consumer, command, *args, "--output", package)
            assert forbidden.returncode == 1
    assert before == fingerprint()


def test_installed_boundary_and_optional_dependency_contract():
    import omb

    if not os.environ.get("OMB_EXPECT_INSTALLED"):
        pytest.skip("installed environment assertion")
    assert "site-packages" in Path(omb.__file__).parts
    assert (Path(omb.__file__).parent / "data/artifacts/catalog-v001.xml").is_file()
    assert (Path(omb.__file__).parent / "py.typed").is_file()
    if os.environ.get("OMB_EXPECT_PUBLISH") == "1":
        import omb.uploaders.fc_upload_with_update
    else:
        assert importlib.util.find_spec("keycloak") is None


def test_negative_fixture_errors_are_reported_without_recording(consumer):
    data = write_data(consumer)
    data.write_text("{broken", encoding="utf-8")
    result = check_negative_fixtures(
        [data], artifacts=[consumer / "artifacts"], update=True
    )
    assert not result.ok and result.failures
    assert not data.with_suffix(".expected").exists()


def test_missing_requested_path_cannot_be_hidden_by_a_valid_one(consumer):
    good = write_data(consumer)
    result = validate_data(
        [good, consumer / "missing.json"], artifacts=[consumer / "artifacts"]
    )
    assert not result.conforms and result.errors
    report = check_negative_fixtures(
        [good, consumer / "missing.json"],
        artifacts=[consumer / "artifacts"],
        update=True,
    )
    assert not report.ok and report.errors


def test_recording_only_conformant_data_does_not_claim_a_negative_fixture(consumer):
    good = write_data(consumer)
    report = check_negative_fixtures(
        [good], artifacts=[consumer / "artifacts"], update=True
    )
    assert not report.ok and report.errors
    assert not good.with_suffix(".expected").exists()


def test_syntax_cli_rejects_malformed_json(consumer):
    data = write_data(consumer)
    data.write_text("{broken", encoding="utf-8")
    result = run_cli(
        consumer,
        "onto-validate",
        "--run",
        "check-syntax",
        "--data-paths",
        data,
        "--offline",
    )
    assert result.returncode == 101, result.stdout + result.stderr
