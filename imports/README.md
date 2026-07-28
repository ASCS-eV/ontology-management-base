# Base Ontologies

Vendored copies of the base vocabularies the ontologies in `artifacts/` build on
(RDF, RDFS, OWL, SKOS, schema.org, DCTerms, PROV, FOAF, DID, VC, …), resolved
locally through `imports/catalog-v001.xml` so validation runs offline and
byte-stably.

All of these were downloaded from the sources named in their respective contexts.
**They are not original works of this project**; the original terms and licenses of
each vocabulary apply. Please refer to the individual license terms.

## ASAM schemas are not here

The normative ASAM XML schemas used to live in `imports/OpenDrive/xsd_schema/` and
`imports/OpenScenario/OpenSCENARIO.xsd`. That predates the standards submodule. They
now live in the one place that pins ASAM deliverables and records their provenance:

| Standard | Path |
|---|---|
| ASAM OpenDRIVE® XSD | `submodules/asam-openx-standards/standards/asam-opendrive/schema/` |
| ASAM OpenSCENARIO® XML XSD | `submodules/asam-openx-standards/standards/asam-openscenario-xml/schema/` |

Those directories carry a provenance README each — standard, version, deliverable,
source URL, retrieval date, SHA-256 checksums — plus ASAM's ownership and
redistribution notice. The submodule holds the matching specification prose, so
schemas and specification can no longer drift apart unnoticed.

Code must reference them through `omb.core.constants`
(`ASAM_OPENDRIVE_SCHEMA_DIR`, `ASAM_OPENSCENARIO_SCHEMA_FILE`), never as literal
paths, and must tolerate their absence: they exist only once the submodule is
initialised.

```bash
git submodule update --init --recursive submodules/asam-openx-standards
```
