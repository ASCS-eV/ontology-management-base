# LinkML Models

Some ontologies are generated from a LinkML schema, the single source of their
OWL ontology, SHACL shapes and JSON-LD context:

| Domain | Schema |
|---|---|
| ontology-header | `linkml/ontology-header/ontology-header.yaml` |
| manifest | `linkml/manifest/manifest.yaml` |
| georeference | `linkml/georeference/georeference.yaml` |
| envited-x | `linkml/envited-x/envited-x.yaml` |
| ositrace | `linkml/ositrace/ositrace.yaml` |
| openlabel-v2 | `linkml/openlabel-v2/openlabel-v2.yaml` |

Their `artifacts/<domain>/` files are generator output and are never edited by
hand. The Gaia-X artifacts (`artifacts/gx/`) are generated from the Gaia-X LinkML
schemas in `submodules/service-characteristics` (`just generate-gx`). The other
domains are hand-written and import the generated ones.

## Building

```bash
just generate                  # every generated domain, in import order
just generate-domain manifest  # one domain
```

`scripts/build_linkml_domain.sh` runs `gen-owl`, `gen-shacl` and
`gen-jsonld-context` with the flags in `linkml/<domain>/gen-flags.env`. It fails
on an empty artifact, on an unexpanded IRI and on any rule or class expression
`gen-shacl` skips, and leaves `artifacts/` untouched when it fails. CI regenerates
every domain and fails on any difference from the committed artifacts.

The generators come from the ASCS-eV LinkML fork, pinned in `pyproject.toml` and
`uv.lock` and installed by `just setup`. envited-x and ositrace import the Gaia-X
LinkML schemas, so `submodules/service-characteristics` must be checked out at its
pinned commit (`git submodule update --init submodules/service-characteristics`).

## Modelling

Each construct is modelled by what it is meant to express, with the LinkML
mechanism designed for it; nothing is pre- or post-processed around the
generators. The headers of manifest, georeference, envited-x and ositrace follow
the ontology-header profile: each instantiates `ontology-header:OntologyHeader`,
which declares the header annotations whose values are IRIs.

[`linkml/GAPS.md`](https://github.com/ASCS-eV/ontology-management-base/blob/main/linkml/GAPS.md)
records the modelling decisions, the open decisions, what the generators cannot
state, and what each generated domain therefore leaves out. Naming follows the
[LinkML Modelling Guidelines](linkml-modelling-guidelines.md).

## Porting a hand-written domain

A domain is ported after the domains it imports. `just verify-linkml <domain>`
builds the schema into a scratch directory and compares the result with the
committed artifacts (`scripts/compare_artifacts.py`): header, vocabulary, JSON-LD
expansion of the test instances, SHACL verdicts, and adversarial instances derived
from the committed shapes.
