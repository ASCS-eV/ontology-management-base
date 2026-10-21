#!/usr/bin/env python3
"""
Agreement between the merged and per-resource validation paths.

FEATURE SET:
============
``per_resource=True`` isolates input documents from one another. It must not
also isolate a document from the resources it points at, or the two paths
disagree about the same file. Both causes of such a disagreement are covered
here: an external reference that only the catalog can resolve, and an
individual that only the ontology declares.

USAGE:
======
pytest tests/integration/test_per_resource_parity.py

NOTES:
======
The repository is built in a tmp_path, so the test is fast and independent of
the repository's own artifacts and catalogs.
"""

import json
from pathlib import Path

import pytest

from omb.api import validate_data

NS = "https://example.org/widget/v1/"
OWNER_DID = "did:web:test.example.net:Owner:acme"

OWL = f"""@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix w: <{NS}> .
w: a owl:Ontology .
w:Widget a owl:Class .
w:Owner a owl:Class .
w:Category a owl:Class .
w:LicenseCategory a owl:Class ; rdfs:subClassOf w:Category .
w:isLicense a w:LicenseCategory, owl:NamedIndividual .
w:category a owl:ObjectProperty ; rdfs:range w:Category .
w:ownedBy a owl:ObjectProperty ; rdfs:range w:Owner .
w:name a owl:DatatypeProperty .
"""

SHAPES = f"""@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix w: <{NS}> .
w:WidgetShape a sh:NodeShape ; sh:targetClass w:Widget ;
    sh:property [ sh:path w:category ; sh:class w:LicenseCategory ; sh:minCount 1 ] .
w:OwnerShape a sh:NodeShape ; sh:targetClass w:Owner ;
    sh:property [ sh:path w:name ; sh:minCount 1 ] .
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A miniature repository: one domain, one catalogued fixture, one document."""
    artifacts = tmp_path / "artifacts" / "widget"
    artifacts.mkdir(parents=True)
    (artifacts / "widget.owl.ttl").write_text(OWL, encoding="utf-8")
    (artifacts / "widget.shacl.ttl").write_text(SHAPES, encoding="utf-8")
    (artifacts / "widget.context.jsonld").write_text(
        json.dumps({"@context": {"@vocab": NS}}), encoding="utf-8"
    )

    fixtures = tmp_path / "tests" / "fixtures"
    fixtures.mkdir(parents=True)
    # Only the catalog knows where the owner is described.
    (fixtures / "owner.json").write_text(
        json.dumps(
            {
                "@context": {"@vocab": NS},
                "@id": OWNER_DID,
                "@type": "Owner",
                "name": "Acme",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "tests" / "catalog-v001.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">\n'
        f'  <uri name="{OWNER_DID}" uri="tests/fixtures/owner.json" '
        'domain="fixture" test-type="fixture" category="fixture"/>\n'
        "</catalog>\n",
        encoding="utf-8",
    )

    data = tmp_path / "data" / "widget.json"
    data.parent.mkdir()
    data.write_text(
        json.dumps(
            {
                "@context": {"@vocab": NS},
                "@id": "urn:item:widget",
                "@type": "Widget",
                # Declared by the ontology, never described by the data.
                "category": {"@id": f"{NS}isLicense"},
                # Described by a fixture the catalog resolves.
                "ownedBy": {"@id": OWNER_DID},
            }
        ),
        encoding="utf-8",
    )
    return tmp_path


def _validate(repo: Path, per_resource: bool):
    return validate_data(
        [repo / "data" / "widget.json"],
        artifacts=[repo / "artifacts"],
        root_dir=repo,
        per_resource=per_resource,
    )


def test_both_paths_accept_the_same_document(repo: Path):
    """The same file, the same shapes, so the same verdict.

    Per-resource validation used to skip reference resolution and to withhold
    the ontology's own individuals, which turned a resolvable reference and a
    declared category into ``minCount`` and ``sh:class`` violations that the
    merged path never reported.
    """
    merged = _validate(repo, per_resource=False)
    isolated = _validate(repo, per_resource=True)

    assert merged.conforms, merged.report_text
    assert isolated.conforms, [str(v) for v in isolated.violations] or (
        isolated.report_text
    )
    assert isolated.violations == merged.violations == []


def test_both_paths_still_reject_a_real_violation(repo: Path):
    """Agreement is not silence: a genuinely bad reference fails on both paths."""
    (repo / "tests" / "fixtures" / "owner.json").write_text(
        json.dumps({"@context": {"@vocab": NS}, "@id": OWNER_DID, "@type": "Owner"}),
        encoding="utf-8",
    )

    merged = _validate(repo, per_resource=False)
    isolated = _validate(repo, per_resource=True)

    assert not merged.conforms and not isolated.conforms
    assert (
        [v.component for v in isolated.violations]
        == [v.component for v in merged.violations]
        == ["MinCountConstraintComponent"]
    )


def test_isolation_between_input_documents_is_kept(repo: Path):
    """Resolving references must not reintroduce cross-document merging.

    Two documents describing the SAME subject are the case per-resource
    validation exists for: merged into one graph they lend each other the
    properties they are missing, so a document with no category passes on
    another's. Reference resolution leaves this untouched, because a fixture is
    merged only for an IRI the document does not describe itself.
    """
    second = repo / "data" / "widget_without_category.json"
    second.write_text(
        json.dumps(
            {
                "@context": {"@vocab": NS},
                "@id": "urn:item:widget",
                "@type": "Widget",
                "ownedBy": {"@id": OWNER_DID},
            }
        ),
        encoding="utf-8",
    )

    merged = validate_data(
        [repo / "data"], artifacts=[repo / "artifacts"], root_dir=repo
    )
    isolated = validate_data(
        [repo / "data"],
        artifacts=[repo / "artifacts"],
        root_dir=repo,
        per_resource=True,
    )

    assert merged.conforms, "merging is what hides the missing category"
    assert not isolated.conforms
    assert [Path(v.file).name for v in isolated.violations] == [second.name]
