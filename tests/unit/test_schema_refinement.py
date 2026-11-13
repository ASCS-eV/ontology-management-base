#!/usr/bin/env python3
"""Refinement-proof gate for JSON-Schema -> LinkML migrations.

Asserts, for every `proof_spec.yaml` under linkml/, that the LinkML-generated
JSON Schema is a *sound refinement* of its normative reference JSON Schema:
everything the LinkML schema accepts, the reference schema also accepts --
except for the bounded, declared relaxations (Λ) named in the spec, each bound
to the locations it may occur at.

This is the machine-checked counterpart to the curated examples in
tests/unit/test_openlabel_schema.py::TestFunctionalEquivalence. The prover
(scripts/schema_refinement_prover.py) derives scope by $ref reachability, walks
both schemas for a structural gap table, and runs a differential oracle over a
mutation + property-based corpus. Its own mechanics are unit-tested in
tests/unit/test_schema_refinement_prover.py.
"""

import copy
import json
import os
import sys
from functools import cache
from pathlib import Path

import pytest
import yaml

from omb.core.constants import ASAM_SUBMODULE_HINT

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import schema_refinement_prover as prover  # noqa: E402

# The property-based corpus makes this suite minutes-scale; mark it slow so a
# fast lane (`pytest -m 'not slow'`) can skip it without weakening the gate.
pytestmark = pytest.mark.slow

# Every migration proof spec in the repository is gated.
PROOF_SPECS = sorted((ROOT_DIR / "linkml").glob("*/proof_spec.yaml"))
OPENLABEL_SPEC = ROOT_DIR / "linkml" / "openlabel-tagging" / "proof_spec.yaml"


def _spec(spec_path: Path) -> dict:
    """Load *spec_path*, or skip/fail when its reference schema is absent.

    The normative reference schema lives in a ~260 MB submodule that the cheap
    test matrix deliberately does not check out, so skipping is right there. The
    ``Pinned Standards Drift`` job fetches the submodule and sets
    ``OMB_REQUIRE_PINNED_SOURCES=1``; there a missing file must fail instead,
    because a refinement gate that quietly stops running is precisely the
    vacuity this suite exists to rule out.
    """
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    reference = ROOT_DIR / spec["reference_schema"]
    if not reference.exists():
        if os.environ.get("OMB_REQUIRE_PINNED_SOURCES"):
            raise AssertionError(
                f"{reference} is missing while OMB_REQUIRE_PINNED_SOURCES is set. "
                f"{ASAM_SUBMODULE_HINT}"
            )
        pytest.skip(f"{reference} not checked out. {ASAM_SUBMODULE_HINT}")
    return spec


@cache
def _report(spec_path: Path) -> prover.ProofReport:
    """The proof for *spec_path*, computed once per test session (~1 min)."""
    return prover.prove(_spec(spec_path), ROOT_DIR)


@pytest.fixture(params=PROOF_SPECS, ids=lambda p: p.parent.name)
def spec_path(request) -> Path:
    return request.param


@pytest.fixture
def report(spec_path: Path) -> prover.ProofReport:
    return _report(spec_path)


def test_specs_exist() -> None:
    """At least the OpenLABEL scenario-tagging profile must declare a proof spec."""
    assert PROOF_SPECS, "no */proof_spec.yaml found under linkml/"
    assert OPENLABEL_SPEC in PROOF_SPECS


class TestRefinementProof:
    """The core scientific claim: L is a sound refinement of A within scope."""

    def test_soundness_no_undisclosed_looser(self, report: prover.ProofReport) -> None:
        """Soundness corpus (L-grammar + mutations): nothing L accepts may be
        rejected by A for an undeclared reason or at an undeclared location.
        One counterexample refutes it."""
        offenders = report.soundness.linkml_looser
        assert not offenders, (
            f"{report.name}: {len(offenders)} instance(s) accepted by LinkML but "
            f"rejected by the reference schema for an UNDISCLOSED reason "
            f"(refutes soundness): {offenders[:5]}"
        )

    def test_completeness_no_undisclosed_looser(
        self, report: prover.ProofReport
    ) -> None:
        """Completeness corpus (A|τ-valid instances) must never expose undisclosed
        looseness either."""
        assert not report.completeness.linkml_looser

    def test_every_in_scope_def_is_modelled(self, report: prover.ProofReport) -> None:
        """No in-scope reference definition may be left without a LinkML mapping."""
        assert not report.unmapped, (
            f"{report.name}: in-scope defs with no LinkML counterpart: {report.unmapped}"
        )

    def test_no_structural_looser_rows(self, report: prover.ProofReport) -> None:
        """No gap row may say L is looser than A. A row describes a whole
        definition, so no location-bound declaration can cover it."""
        rows = report.structural_looser
        assert not rows, (
            f"{report.name}: structural looseness: {[(g.ref_def, g.aspect) for g in rows]}"
        )

    def test_every_declared_relaxation_is_needed(
        self, report: prover.ProofReport
    ) -> None:
        """A declaration nothing needs still widens what the gate accepts. When
        its cause is fixed (e.g. the generator stops emitting the null branch),
        this fails until the declaration is removed."""
        assert not report.unobserved_relaxations

    def test_verdict_proven(self, report: prover.ProofReport) -> None:
        """End-to-end: a proven sound refinement whose declared relaxations are
        all needed."""
        assert report.passes, f"{report.name}: verdict = {report.verdict()}"

    def test_corpus_is_complete(
        self, spec_path: Path, report: prover.ProofReport
    ) -> None:
        """Guard against a vacuous or quietly shrunken proof: every requested
        property-based instance was generated and the seeds were mutated."""
        budget = _spec(spec_path).get("hypothesis", {})
        sizes = report.corpus_sizes
        assert sizes["seeds"] > 0
        assert sizes["mutations"] > sizes["seeds"]
        assert sizes["hypothesis_soundness"] == budget.get("soundness", 0)
        assert sizes["hypothesis_completeness"] == budget.get("completeness", 0)
        assert report.soundness.agree_accept > 0

    def test_committed_report_is_current(
        self, spec_path: Path, report: prover.ProofReport
    ) -> None:
        """REFINEMENT_PROOF.md is what the prover produces today.

        The property-based corpus is reproducible only under the Python and
        Hypothesis versions the report names (CI's Pinned Standards Drift job,
        and `just refinement-proof`). Under other versions the comparison would
        measure the environment, so it is skipped -- unless the pinned sources
        are required, where a mismatch means the report needs regenerating."""
        committed = spec_path.parent / "REFINEMENT_PROOF.md"
        recorded = committed.read_text(encoding="utf-8")
        if f"generated with {report.environment};" not in recorded:
            message = (
                f"{committed.name} was not generated with {report.environment}. "
                "Regenerate it with `just refinement-proof`."
            )
            if os.environ.get("OMB_REQUIRE_PINNED_SOURCES"):
                raise AssertionError(message)
            pytest.skip(message)
        spec = _spec(spec_path)
        allowed = prover.parse_relaxations(spec.get("allow_looseness"))
        expected = prover.report_markdown(
            report, allowed, spec.get("justifications", {})
        )
        assert recorded == expected, (
            f"{committed} is stale. Regenerate it with `just refinement-proof`."
        )


class TestOpenLabelProof:
    """Pin the OpenLABEL scenario-tagging proof so scope drift is caught."""

    @pytest.fixture
    def ol(self) -> prover.ProofReport:
        return _report(OPENLABEL_SPEC)

    def test_in_scope_defs(self, ol: prover.ProofReport) -> None:
        assert set(ol.in_scope) == {
            "attributes",
            "boolean",
            "metadata",
            "num",
            "ontologies",
            "resource_uid",
            "resources",
            "tag",
            "tag_data",
            "text",
            "vec",
        }

    def test_multisensor_defs_out_of_scope(self, ol: prover.ProofReport) -> None:
        """The labeling containers (spec 8.1: not used for tagging) stay excluded."""
        out = set(ol.out_scope)
        for d in ("object", "frame", "stream", "bbox", "cuboid", "poly2d", "transform"):
            assert d in out, f"{d} should be out of tagging scope"

    def test_key_patterns_are_enforced(self) -> None:
        """key_pattern is never declared: every UID-keyed section enforces ASAM's
        key patterns, so an instance accepted on a bad key refutes the proof."""
        spec = _spec(OPENLABEL_SPEC)
        assert prover.KEY_PATTERN not in spec["allow_looseness"]

    def test_gate_refutes_a_dropped_key_pattern(self, tmp_path: Path) -> None:
        """The gate has teeth on the real schemas: drop the tag key pattern from
        the published schema and the mutation corpus alone refutes the proof."""
        spec = _spec(OPENLABEL_SPEC)
        loose = json.loads((ROOT_DIR / spec["linkml_schema"]).read_text("utf-8"))
        del loose["$defs"]["OpenLabel"]["properties"]["tags"]["propertyNames"]
        (tmp_path / "loose.json").write_text(json.dumps(loose), encoding="utf-8")
        spec = copy.deepcopy(spec)
        spec["linkml_schema"] = str(tmp_path / "loose.json")
        spec["hypothesis"] = {"soundness": 0, "completeness": 0}
        report = prover.prove(spec, ROOT_DIR)
        assert not report.sound
        assert any(
            ":rekey:" in c["case"] and "['tags']" in c["case"]
            for c in report.soundness.linkml_looser
        )
