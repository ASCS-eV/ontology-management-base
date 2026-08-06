# ASAM OpenDRIVE® — derived vocabulary

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
| `opendrive.owl.ttl` | `standards/asam-opendrive/generated/` | OWL 2 ontology, generated from ASAM's open UML model |
| `opendrive.shacl.ttl` | `standards/asam-opendrive/generated/` | SHACL shapes, generated from that ontology |
| `schema/OpenDRIVE_*.xsd` | `standards/asam-opendrive/schema/` | ASAM's **normative** XML schema, as published |

The ontology and the shapes are *generated artifacts*, not normative ASAM deliverables. The
XSD is the normative deliverable. Where they disagree, the XSD wins — see
[the equivalence check](#relationship-to-the-normative-schema).

## Provenance

The submodule is the single place that records where these came from: the ASAM standard and
version, the deliverable, the source URL, the retrieval date and a SHA-256 for every schema
file, plus ASAM's ownership and redistribution notice. That record is not duplicated here,
because a second copy of a provenance statement is a second thing to keep true. See:

- `submodules/asam-openx-standards/standards/asam-opendrive/schema/README.md` — schema provenance
- `submodules/asam-openx-standards/standards/asam-opendrive/generated/provenance.json` — what
  produced the OWL/SHACL: source model checksum, tool commits, ruleset, and the pinned
  serialization stack
- `submodules/asam-openx-standards/pipeline/README.md` — how the generation works and why each
  stage is configured as it is

The XML schemas are copied as raw bytes, CRLF included, so that ASAM's published checksums
verify against these files unchanged. `.gitattributes` and the `mixed-line-ending` pre-commit
hook both exempt `imports/*/schema/` for that reason.

## Why the copy exists

`imports/catalog-v001.xml` maps an ontology IRI to a local file using paths relative to
`imports/`, so it cannot point into the submodule. Without a copy here, nothing resolves
`http://code.asam.net/simulation/standard/opendrive` offline. The copy also means a checkout
without `--recurse-submodules` still has the vocabularies.

## How it is used

Registered in `imports/catalog-v001.xml` under two IRIs:

| IRI | Resolves to |
|---|---|
| `http://code.asam.net/simulation/standard/opendrive` | `opendrive/opendrive.owl.ttl` |
| `http://code.asam.net/simulation/standard/opendrive/shapes` | `opendrive/opendrive.shacl.ttl` |

Instance data whose `@type` sits in the OpenDRIVE namespace therefore picks up both the
ontology (for inference) and the shapes (for validation) automatically, through
`RegistryResolver`. No domain in `artifacts/` currently does so; the wiring is in place for
one that will.

## Relationship to the normative schema

`scripts/check_xsd_structural_parity.py` in the submodule regenerates an XSD from the same UML
model and compares it against the normative schema in `schema/`. **Enumeration values match
exactly, file by file** — the strongest available signal that no enumeration was dropped on the
way to OWL, which is the regression the generation pipeline exists to prevent.

Element and attribute counts differ. ASAM's XSD encodes 468 properties as XML attributes and the
generated one encodes none — but **not** because the model omits that information. The EA model
carries the `XSDattribute` stereotype on exactly those 468 properties; the SCXML export drops it,
because it is an EA XML Schema profile stereotype rather than one ShapeChange knows. Recovering it
is an export/tooling question (`asam-openx-standards#11`), not a modelling change to request from
ASAM. Until then the two schemas describe the same content in different XML styles.
`tests/integration/test_asam_imports.py` covers what can be checked without a Java toolchain:
that the copies match the submodule, that both IRIs resolve, and that every class the shapes
target is defined by the ontology.

## License

ASAM OpenDRIVE® is a registered trademark of ASAM e.V. These files are **not** original works
of this project. ASAM permits unrestricted distribution of the standard; the original ASAM
license terms apply. See <https://www.asam.net/license> and the provenance README in the
submodule.
