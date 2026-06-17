#!/usr/bin/env python3
"""Refinement-proof gate for JSON-Schema -> LinkML migrations.

Asserts, for every `proof_spec.yaml` under linkml/, that the LinkML-generated
JSON Schema is a *sound refinement* of its normative reference JSON Schema:
everything the LinkML schema accepts, the reference schema also accepts —
except for the bounded, declared relaxations (Λ) named in the spec.

This is the machine-checked, ontology-independent counterpart to the curated
examples in tests/unit/test_openlabel_schema.py::TestFunctionalEquivalence.
The prover (scripts/schema_refinement_prover.py) derives scope by $ref
reachability, walks both schemas for a structural gap table, and runs a
differential oracle over a mutation + property-based corpus.
"""

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import schema_refinement_prover as prover  # noqa: E402
import yaml  # noqa: E402

# The property-based corpus makes this suite minutes-scale; mark it slow so a
# fast lane (`pytest -m 'not slow'`) can skip it without weakening the gate.
pytestmark = pytest.mark.slow

# Every migration proof spec in the repository is gated.
PROOF_SPECS = sorted((ROOT_DIR / "linkml").glob("*/proof_spec.yaml"))


@pytest.fixture(scope="module", params=PROOF_SPECS, ids=lambda p: p.parent.name)
def report(request) -> prover.ProofReport:
    spec = yaml.safe_load(request.param.read_text(encoding="utf-8"))
    return prover.prove(spec, ROOT_DIR)


def test_specs_exist() -> None:
    """At least the OpenLABEL v2 migration must declare a proof spec."""
    assert PROOF_SPECS, "no */proof_spec.yaml found under linkml/"
    assert any(p.parent.name == "openlabel-v2" for p in PROOF_SPECS)


class TestRefinementProof:
    """The core scientific claim: L is a sound refinement of A within scope."""

    def test_soundness_no_undisclosed_looser(self, report: prover.ProofReport) -> None:
        """Soundness corpus (L-grammar + mutations): nothing L accepts may be
        rejected by A for an undeclared reason. One counterexample refutes it."""
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

    def test_all_structural_looseness_is_declared(
        self, report: prover.ProofReport
    ) -> None:
        """Every LOOSER row in the structural gap table must belong to a declared
        looseness category (Λ); an undeclared one is a soundness gap."""
        undisclosed = report.undisclosed_structural_looser
        assert not undisclosed, (
            f"{report.name}: undisclosed structural looseness: "
            f"{[(g.ref_def, g.aspect) for g in undisclosed]}"
        )

    def test_verdict_proven(self, report: prover.ProofReport) -> None:
        """End-to-end: the migration is a proven sound refinement."""
        assert report.sound, f"{report.name}: verdict = {report.verdict()}"

    def test_corpus_actually_ran(self, report: prover.ProofReport) -> None:
        """Guard against a vacuous proof: the differential corpus must be non-trivial
        and must contain agreement (both-accept) evidence."""
        assert report.soundness.total >= 50
        assert report.soundness.agree_accept > 0


class TestOpenLabelScopeProjection:
    """Pin the OpenLABEL v2 scope so accidental scope drift is caught."""

    @pytest.fixture(scope="class")
    def ol(self) -> prover.ProofReport:
        spec_path = ROOT_DIR / "linkml" / "openlabel-v2" / "proof_spec.yaml"
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        return prover.prove(spec, ROOT_DIR)

    def test_in_scope_defs(self, ol: prover.ProofReport) -> None:
        assert set(ol.in_scope) == {
            "attributes",
            "boolean",
            "metadata",
            "num",
            "ontologies",
            "resource_uid",
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

    def test_disclosed_looseness_is_bounded(self, ol: prover.ProofReport) -> None:
        """Looseness is limited to the two known LinkML-codegen relaxations."""
        breakdown = ol.soundness.looseness_breakdown()
        assert set(breakdown) <= {prover.KEY_PATTERN, prover.NULL_OPTIONAL}
