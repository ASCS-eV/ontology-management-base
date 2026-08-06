# ASAM OpenSCENARIO® XML — derived vocabulary

**Do not edit any file in this directory.** Everything except this README is derived from the
`asam-openx-standards` submodule by `omb/utils/asam_imports.py`, and `--check` compares the
copies byte-for-byte against their source. To change something, change it in the submodule and
re-derive:

```bash
git submodule update --init --recursive submodules/asam-openx-standards
just asam-imports
just registry-update
```

## Contents

| File | Derived from | What it is |
|---|---|---|
| `openscenario.owl.ttl` | `standards/asam-openscenario-xml/generated/` | OWL 2 ontology, generated from ASAM's open UML model |
| `openscenario.shacl.ttl` | `standards/asam-openscenario-xml/generated/` | SHACL shapes, generated from that ontology |
| `schema/OpenSCENARIO.xsd` | `standards/asam-openscenario-xml/schema/` | ASAM's **normative** XML schema, as published |

The ontology and the shapes are *generated artifacts*, not normative ASAM deliverables. The
XSD is the normative deliverable. Where they disagree, the XSD wins — see
[the equivalence check](#relationship-to-the-normative-schema).

Unlike OpenDRIVE, ASAM publishes OpenSCENARIO XML as a **single** schema document rather than a
per-package split, which is why `schema/` holds one file.

## Provenance

The submodule is the single place that records where these came from: the ASAM standard and
version, the deliverable, the source URL, the retrieval date and a SHA-256 for the schema, plus
ASAM's ownership and redistribution notice. See:

- `submodules/asam-openx-standards/standards/asam-openscenario-xml/schema/README.md` — schema provenance
- `submodules/asam-openx-standards/standards/asam-openscenario-xml/generated/provenance.json` —
  what produced the OWL/SHACL: source model checksum, tool commits, ruleset, and the pinned
  serialization stack
- `submodules/asam-openx-standards/pipeline/README.md` — how the generation works and why each
  stage is configured as it is

The XML schema is copied as raw bytes so that ASAM's published checksum verifies against this
file unchanged. `.gitattributes` and the `mixed-line-ending` pre-commit hook both exempt
`imports/*/schema/` for that reason.

## Why the copy exists

`imports/catalog-v001.xml` maps an ontology IRI to a local file using paths relative to
`imports/`, so it cannot point into the submodule. Without a copy here, nothing resolves
`http://code.asam.net/simulation/standard/openscenario` offline. The copy also means a checkout
without `--recurse-submodules` still has the vocabularies.

## How it is used

Registered in `imports/catalog-v001.xml` under two IRIs:

| IRI | Resolves to |
|---|---|
| `http://code.asam.net/simulation/standard/openscenario` | `openscenario/openscenario.owl.ttl` |
| `http://code.asam.net/simulation/standard/openscenario/shapes` | `openscenario/openscenario.shacl.ttl` |

Instance data whose `@type` sits in the OpenSCENARIO namespace therefore picks up both the
ontology (for inference) and the shapes (for validation) automatically, through
`RegistryResolver`.

## Relationship to the normative schema

The generation run is clean in a way OpenDRIVE's is not. The OpenSCENARIO UML model carries no
`targetNamespace` tagged values at all, so exactly one schema package resolves and
`rule-owl-pkg-singleOntologyPerSchema` is satisfied without the 227 errors OpenDRIVE's seven
identically-tagged sub-packages produce. Its 48 `<<union>>` classes also encode without the
supertype defects documented for OpenDRIVE. The pipeline therefore tolerates **no** ShapeChange
errors for this standard: any that appear stop the build.

`scripts/check_xsd_structural_parity.py` in the submodule regenerates an XSD from the same UML
model and compares it against the normative schema. As with OpenDRIVE, element and attribute
counts differ: ASAM's schema declares 448 XML attributes and the generated one none. That is a
loss in the **SCXML export**, which drops the EA XML Schema profile stereotypes the models use to
say which properties are attributes, rather than a gap in the models themselves — see
`imports/opendrive/README.md`, where the correspondence is exact and measurable. Enumeration
values remain the invariant the check enforces.
`tests/integration/test_asam_imports.py` covers what can be checked without a Java toolchain:
that the copies match the submodule, that both IRIs resolve, and that every class the shapes
target is defined by the ontology.

## License

ASAM OpenSCENARIO® is a registered trademark of ASAM e.V. These files are **not** original
works of this project. ASAM permits unrestricted distribution of the standard; the original
ASAM license terms apply. See <https://www.asam.net/license> and the provenance README in the
submodule.
