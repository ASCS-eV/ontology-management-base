# LinkML migration — modelling decisions, gaps and open questions

The ontologies are re-modelled in LinkML by **intent**: each hand-written
construct is traced to what it was meant to express, and that intent is modelled
with the LinkML mechanism designed for it. The generators are the only thing
that runs — nothing is pre- or post-processed — so a construct LinkML cannot
express shows up as a measured gap, never as a patch.

Every entry below is verified against the generator source or with a minimal
schema. Measure a domain with `just verify-linkml <domain>`.

## Status

| Domain | header | vocab | context | shacl | probe (caught / total) | Every remaining difference is |
|---|---|---|---|---|---|---|
| manifest | 11 | OK | 7 | 55 | 11 (139 / 153) | D1; D5 (`filePath`, `iri`, `conformsTo`); D7 (`LicenseLink` category); the JSON-LD artifact rule, not yet modelled |
| georeference | 10 | OK | OK | OK | OK (46 / 46) | D1 |
| envited-x | 11 | 4 | 7 | 23 | 20 (184 / 196) | D1; `rdfs:subClassOf owl:Thing` ×4, not expressible and semantically empty; D11 (bare class terms); the envited-x link vocabulary and narrowings, not yet modelled (×7 probes); via manifest: D5 (×12 probes), D7, and the JSON-LD artifact rule (×1 probe) |
| ositrace | 10 | OK | OK | 14 | 3 (594 / 604) | D1; D5 (`validationReport`: `sh:nodeKind sh:IRI` on its literal values, ×4 instances, ×3 probes); G7 (an invalid channel or format is reported on its own shape, not also through `sh:or` / `sh:node` up the chain) |

Measured per resource (R2), so a probe counts only when it adds a violation to
its unmutated instance. envited-x is measured together with the candidate
manifest (`--with manifest=…`), whose `LicenseLink` it inherits.

Layers: `header` (ontology node), `vocab` (classes, properties, axioms),
`context` (JSON-LD expansion of every test instance), `shacl` (verdict and
violations per test instance), `probe` (adversarial instances derived from every
committed shape, judged by the violations a mutation *adds*).

---

## Modelling mechanisms

**M1 — Dependencies are imported, as CURIEs.** A class or property owned by
another ontology is never restated or stood in for locally; its schema is
imported. The import is written as a CURIE whose prefix plus local name is the
dependency's `id` (`envitedx_ontology:v3`), the idiom LinkML itself uses for
`linkml:types`. gen-owl then emits the correct `owl:imports` IRI, and
`--no-mergeimports` / `--exclude-imports` keep the dependency's own classes and
shapes out of the domain's artifacts. An absolute-IRI import is not usable for a
dependency that has relative imports of its own (G9).

**M2 — Specialisation is `is_a`, for classes and for slots.** Class `is_a`
yields `rdfs:subClassOf`; slot `is_a` yields `rdfs:subPropertyOf`
(`owlgen.py:1088`). `subproperty_of` is **not** the property hierarchy: the
metamodel defines it as a value set ("any ontological child … is a valid value
for the slot"), which is why gen-shacl renders it as `sh:in`.

**M3 — Inherit, never restate.** Slots defined upstream (Gaia-X `license`,
`copyrightOwnedBy`, `name`, …) are listed by name on the extending class, not
redeclared with `slot_uri`. They keep the upstream IRI in every artifact.

**M4 — Name collisions: unique LinkML name, published IRI and JSON term
unchanged.** LinkML element names are global across an import closure.
Where two schemas in one closure use the same local name:

- `class_uri` / `slot_uri` keep the published IRI — honoured by gen-owl only
  with `--no-use-native-uris` (always passed by the build).
- `alias` keeps the JSON-LD term, so no instance changes.
- Where one side is an abstract base that no instance is typed with, the base
  takes the prefixed name: envited-x's facet bases are `EnvitedXContent`,
  `EnvitedXFormat`, …, leaving `Content`, `Format`, … free for every domain.

Collisions resolved this way: manifest `conformsTo`/`fileSize` and georeference
`country`/`region` against Gaia-X; ositrace `description`/`formatType`/
`identifier`/`version` against Gaia-X; the envited-x facet bases and
`Manifest` against the domains and manifest.

**M5 — Choices.** "Inline object or link" is slot-level `any_of` over the two
classes (rendered `sh:or ( [sh:class A] [sh:class B] )`). "One of two profiles"
and "at least one of" are class-level `any_of` with `slot_conditions` — the
complete statement of the intent, rendered by gen-owl (`owl:unionOf`) and by
gen-shacl (`sh:or` over the member shapes; a member it cannot translate makes
it skip the whole operator, and the build fails on that).

**M6 — Conditional constraints are `rules`.** The fork's converter
(`--emit-rules`, on by default) translates: conditional-required,
conditional-absent, presence-implies-value, exclusive-value, numeric-threshold
preconditions, one-hop nested preconditions (`range_expression.slot_conditions`)
and `has_member` postconditions — one postcondition per rule. A rule it cannot
translate is skipped, and the build fails on that (G2).

**M7 — Closed value sets are enums.** Road types, lane types, OSI message types
and the like are standardised closed sets; an enum is correct and renders as
`sh:in`.

**M8 — Header from schema metadata.** `description` becomes `rdfs:comment`
under `--metadata-profile rdfs`; `see_also` and `source` give `rdfs:seeAlso` and
`dcterms:source`. `owl:versionInfo` and `dcterms:creator` are literal-valued
annotations. What cannot be expressed is D1.

**M9 — Narrowing is a subclass.** "A license link is a link whose category is a
license category" is `LicenseLink is_a Link` with a narrowed slot. Because the
property declares `rdfs:range manifest:LicenseLink`, RDFS inference types the
node and no instance changes.

**M10 — Declare the prefixes a schema's shapes use.** `xsd:` and, where
schema.org terms are constrained, `sdo:` (never `schema:` — LinkML's built-in
types bind it to `http://schema.org/`). Required under `--exclude-imports` (G13).

---

## Open decisions

**D1 — IRI-valued header terms.** Annotations are always emitted as literals
(`owlgen.py`, annotation loop: `Literal(v.value)`), and `rdfs:label` comes from
the schema `name`. Not expressible: `owl:versionIRI`, `owl:priorVersion`,
`dcterms:identifier`, `dcterms:conformsTo`, `prov:wasDerivedFrom`,
`dcterms:references`, structured `dcterms:contributor` nodes, and a plain
`owl:versionInfo` alongside `@en`-tagged literals (`--default-language` is
global). *Choose:* extend owlgen so annotations can carry an IRI, or reduce the
header profile the repository requires.

**D5 — `xsd:anyURI`: literal or IRI node.** gen-owl and gen-jsonld-context emit
an `xsd:anyURI` literal by default and an IRI node with `--xsd-anyuri-as-iri`;
gen-shacl always emits `sh:nodeKind sh:IRI` for a `uri` range. The committed
ontologies need both behaviours in one schema — `manifest:filePath` and
`ositrace:validationReport` are literals (relative paths must not be resolved
against a document base, and 51 instance values carry
`"@type": "xsd:anyURI"`), `manifest:iri` and `sh:conformsTo` are IRI nodes.
With the flag off, the candidate rejects every such value and so cannot
discriminate a bad one. Deliberately deferred.

**D7 — Access-role and category vocabularies.** The intent differs by level.
At the manifest level the vocabulary is open: `manifest:LinkShape` checks
`sh:class manifest:Category`, and envited-x adds its own categories. At the
envited-x level it is closed: `ExtendedLinkShape` restricts an ENVITED-X link to
exactly three access roles and eight categories (`sh:in`). An enum is therefore
right for envited-x (an `ExtendedLink` narrowing, rendered `sh:in`) and wrong
for manifest, because an enum closes its class with `owl:oneOf`
(`owlgen.py:1255`). Individuals of manifest's open class are instance data in
LinkML terms. *Choose:* how envited-x's enum is anchored so its individuals are
still `manifest:Category`s, and whether manifest's individuals are published as
LinkML instance data. Until then `LicenseLink`'s narrowed category cannot be
satisfied by categories an instance only types as `manifest:Category`.

**D11 — Bare class terms in the envited-x context.** The seven renamed envited-x
classes (M4) lose their bare context terms (`Content`, `Format`, `Manifest`, …).
No instance uses a bare class name, and every instance expands to the same RDF.
`alias` exists for slots only, so this cannot be avoided (G10).

---

## Generator gaps

| | Gap | Consequence | Candidate fix |
|---|---|---|---|
| G2 | rule converter: `value_presence: ABSENT` is not supported as a *precondition*; skipped at DEBUG | "no channels ⇒ `formatType` required" cannot be written as a rule | extend the converter (our fork) |
| G3 | gen-shacl narrows slot-level `exactly_one_of` to the default range, silently | a `string` or `integer` choice rejects integers | render as `sh:xone` |
| G4 | slot-level `has_member` is ignored (supported only inside rules) | — | render as `sh:qualifiedValueShape` |
| G5 | `path_rule` and `inverse` are in the metamodel but not rendered | constraints over property paths — manifest's exemption of its self-reference, which depends on the incoming `hasManifestReference` edge — cannot be expressed | render derived-slot paths as `sh:path` sequences / `sh:inversePath` |
| G6 | every class shape gets `sh:targetClass` | no target-less reusable shapes; handled by M9 instead | — |
| G7 | class ranges are always `sh:class`, never `sh:node` | nested validation depends on the value's type, supplied by the instance or by `rdfs:range` inference | — |
| G8 | the metamodel has no exclusive numeric bounds | `manifest:width > 0` becomes `>= 0` at best | metamodel change |
| G9 | linkml_runtime resolves a dependency's relative imports against its IRI with `os.path.normpath`, collapsing `https://` to `https:/` | no schema with relative imports can be imported by absolute IRI; M1 avoids it | use `urljoin` in `imports_closure` |
| G10 | `alias` has `domain: slot_definition` | a class cannot keep a context term that differs from its LinkML name (D11) | metamodel change |
| G11 | annotations are always literals | D1 | allow a typed annotation value |
| G12 | `types.yaml` documents `uri` as a literal "unless it is an identifier", while `rdflib_dumper` and `shaclgen` emit IRI nodes | the normative contract is unclear (D5) | documentation change in `types.yaml` stating the actual contract |
| G13 | with `--exclude-imports`, gen-shacl no longer knows prefixes declared only in imported schemas: datatype and path CURIEs from `linkml:types` (`xsd:`) or Gaia-X (`sdo:`) are emitted unexpanded, e.g. `sh:datatype <xsd:float>`, which no value matches | silently rejects every value of those slots | expand with the full closure's namespaces; schemas declare the prefixes their shapes use (`xsd:`, `sdo:`) |

---

## Not yet modelled

- **envited-x links.** `ExtendedLink` (closed access-role and category enums,
  D7), the manifest-reference and license-reference narrowings, and
  `ManifestShape`'s "at least one artifact per required category" (`has_member`
  rules, M6).
- **manifest's JSON-LD artifact rule.** "An RDF/JSON-LD artifact link needs
  `iri`, `skos:note` and `sh:conformsTo`" is a nested-precondition rule (M6).
  The committed shape exempts the manifest's self-reference by its *incoming*
  `hasManifestReference` edge, which is not expressible (G5); modelling the
  self-reference as its own class exempts it structurally instead.

## Repository findings outside LinkML

- **R1.** Per-resource inference (`_abox_inference`) applies rdfs3 to every
  non-literal object, blank nodes included, exactly as `apply_rdfs_inference`
  does. Generated shapes depend on it: they use `sh:class`, and inline values are
  blank nodes typed only through `rdfs:range`. A unit test in
  `tests/unit/validators/shacl/test_inference.py` pins both paths to the same
  result.
- **R2.** Per-resource validation merges neither fixtures nor the
  ontology into the data graph. External references (did:web fixtures) are
  typed by `rdfs:range` and then validated without their data, and individuals
  declared in the OWL (`manifest:isLicense a manifest:LicenseCategory`) are
  invisible to `sh:class`. Committed valid instances of automotive-simulator,
  ositrace and manifest are rejected in `--per-resource` mode; the default
  merged mode accepts them.
- **R3.** `manifest.owl.ttl` types `manifest:isMiscellaneous` with the
  undefined `manifest:Miscellaneous`; the class is `manifest:MiscellaneousCategory`.
- **R4.** `artifacts/openlabel-v2/` is generated without
  `--no-use-native-uris`, so its OWL declares `openlabel_v2:QuantitativeValue`,
  `openlabel_v2:minValue` and `openlabel_v2:maxValue` while its SHACL uses
  `schema:QuantitativeValue` (16×), `schema:minValue` and `schema:maxValue`.
- **R5.** manifest and envited-x each define `isManifest`, `isLicense`,
  `isMiscellaneous` and `isPublic` — two IRIs per concept.

## Harness

`scripts/compare_artifacts.py` validates per resource, which shares the loaded
schemas across files but is affected by R2. The probe layer therefore does not
compare verdicts: a probe counts as caught on a side only if it *adds* a
violation to those of the unmutated instance. Probes are derived in RDF space
from every committed shapes file, so constraints contributed by other domains
are exercised, and node-level `sh:or` groups of required paths get their own
"none of" probe. Violations are compared as (focus IRI, path, component);
blank focus nodes are reduced to `_`, so a second violation of the same path
and component on another blank node is not distinguished.
