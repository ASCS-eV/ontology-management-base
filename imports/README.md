# Base Ontologies

Vendored copies of the base vocabularies the ontologies in `artifacts/` build on
(RDF, RDFS, OWL, SKOS, schema.org, DCTerms, PROV, FOAF, DID, VC, …), resolved
locally through `imports/catalog-v001.xml` so validation runs offline and
byte-stably.

All of these were downloaded from the sources named in their respective contexts.
**They are not original works of this project**; the original terms and licenses of
each vocabulary apply. Please refer to the individual license terms.

## The ASAM vocabularies are derived, not maintained

`imports/opendrive/` and `imports/openscenario/` are the exception to everything above:
they are not downloaded from a source named in a context, they are **derived from the
`asam-openx-standards` submodule** and must never be edited in place. Each holds an OWL
ontology, SHACL shapes and ASAM's normative XML schema, with a README of its own.

| | Source of truth |
|---|---|
| Normative XML schemas | `submodules/asam-openx-standards/standards/*/schema/` |
| Generated OWL + SHACL | `submodules/asam-openx-standards/standards/*/generated/` |

The submodule is where provenance lives — standard, version, deliverable, source URL,
retrieval date, SHA-256 checksums, ASAM's ownership and redistribution notice — together
with the matching specification prose and the pipeline that produced the OWL and SHACL.

Re-derive after bumping the submodule:

```bash
git submodule update --init --recursive submodules/asam-openx-standards
just asam-imports                         # copy from the submodule
just asam-imports-check                   # verify byte-for-byte; CI runs this
just registry-update                      # register in catalog-v001.xml
```

`tests/integration/test_asam_imports.py` fails if the copies and the submodule disagree,
so a submodule bump that was not followed by a sync cannot pass unnoticed.

Code that needs the **normative schemas** must reference them through
`omb.core.constants` (`ASAM_OPENDRIVE_SCHEMA_DIR`, `ASAM_OPENSCENARIO_SCHEMA_FILE`),
which point at the submodule, never as literal paths, and must tolerate their absence:
there they exist only once the submodule is initialised. The copies under `imports/` are
committed and so are always present.
