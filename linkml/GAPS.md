# LinkML models — modelling decisions, gaps and open questions

The ontologies are re-modelled in LinkML by **intent**: each hand-written
construct is traced to what it was meant to express, and that intent is modelled
with the LinkML mechanism designed for it. The generators are the only thing
that runs — nothing is pre- or post-processed — so a construct LinkML cannot
express shows up as a measured gap, never as a patch.

Every entry below is verified against the generator source or with a minimal
schema. Fixture validation is evidence about the fixtures; it does not prove
that two models accept the same data or entail the same axioms.

## Status

`ontology-header`, `manifest`, `georeference`, `envited-x`, `ositrace` and
`openlabel-v2` are generated from `linkml/<domain>/<domain>.yaml` by `just generate` (through
`scripts/build_linkml_domain.sh` and `linkml/<domain>/gen-flags.env`); their
`artifacts/<domain>/` files are never edited by hand. The other domains are
hand-written and import them.

What the generated artifacts cannot state, per domain:

| Domain | Remaining |
|---|---|
| ontology-header | G16; G17; G18; G22 |
| manifest | G8 (`width`, `height`, `depth` greater than 0); G16; G17; G19; G21; G22 |
| georeference | G16; G22 |
| envited-x | D11 (bare class terms); G16; G19; G21; G22 |
| ositrace | D5; G16; G22 |
| openlabel-v2 | G20 (`minValue` ≤ `maxValue`) |

The generators come from the ASCS-eV LinkML fork, pinned in `uv.lock`. Besides
upstream LinkML the models use these fork features: `has_member` as
`sh:qualifiedValueShape`, `range_expression` applied to each value, class-level
boolean expressions, the rule-to-SPARQL converter, `instantiates` on schema
resources and permissible values, declared annotation ranges, string-derived
`xsd:anyURI` types as literals, `--normalize-prefixes` and `--diff-stable`.

---

## Modelling mechanisms

**M1 — Dependencies are imported by their `id`.** A class or property owned by
another ontology is never restated or stood in for locally; its schema is
imported. The import names the dependency's `id`, either as a CURIE whose
prefix plus local name expands to it (`envitedx_ontology:v4`, the idiom LinkML
itself uses for `linkml:types`) or as the absolute IRI, and `importmap.json`
points it at the local schema. gen-owl then emits the correct `owl:imports`
IRI, and `--no-mergeimports` / `--exclude-imports` keep the dependency's own
classes and shapes out of the domain's artifacts.

**M2 — Specialisation is `is_a`, for classes and for slots.** Class `is_a`
yields `rdfs:subClassOf`; slot `is_a` yields `rdfs:subPropertyOf`.
`subproperty_of` is **not** the property hierarchy: the metamodel defines it as
a value set ("any ontological child … is a valid value for the slot"), which is
why gen-shacl renders it as `sh:in`. A super-property whose sub-properties have
different ranges takes the union of them as its own range
(`envited-x:hasResourceDescription`), and each class narrows it to its own in
`slot_usage`.

**M3 — Inherit, never restate.** Slots defined upstream (Gaia-X `license`,
`copyrightOwnedBy`, `name`, …) are listed by name on the extending class, not
redeclared with `slot_uri`. They keep the upstream IRI in every artifact.

**M4 — Name collisions: unique LinkML name, published IRI and JSON term
unchanged.** LinkML element names are global across an import closure.
Where two schemas in one closure use the same local name:

- `class_uri` / `slot_uri` keep the published IRI — honoured by gen-owl only
  with `--no-use-native-uris`, which the build passes for every domain.
- `alias` keeps the JSON-LD term, so no instance changes.
- Where one side is an abstract base that no instance is typed with, the base
  takes the prefixed name: envited-x's facet bases are `EnvitedXContent`,
  `EnvitedXFormat`, …, leaving `Content`, `Format`, … free for every domain.

**M5 — Choices.** "Inline object or link" is slot-level `any_of` over the two
classes. "One of two profiles" and "at least one of" are class-level `any_of`
with `slot_conditions` — the complete statement of the intent, rendered by
gen-owl (`owl:unionOf`) and by gen-shacl (`sh:or` over the member shapes; a
member it cannot translate makes it skip the whole operator, and the build fails
on that).

**M6 — Conditional constraints are `rules`.** The rule converter (on by
default) translates conditional-required, conditional-absent (including an
`ABSENT` precondition), presence-implies-value, exclusive-value,
numeric-threshold preconditions, one-hop nested preconditions
(`range_expression.slot_conditions`) and `has_member` postconditions. On a
multivalued slot a precondition such as `equals_string` holds only if **every**
value matches; "one of the values is X" is `has_member: {equals_string: X}`. A
rule the converter cannot translate is skipped, and the build fails on that
(G14).

**M7 — Closed value sets are enums.** Road types, lane types, OSI message types
and the like are standardised closed sets; an enum is correct and renders as
`sh:in`.

**M8 — Header from schema metadata.** The schema `id` is the ontology IRI of
the version (`…/manifest/v6`), as in every hand-written ontology of this
repository; `owl:versionIRI` would only repeat it, and OWL 2 makes it
ontology-header structure, not an annotation, so it is not stated (G22).
`description` becomes `rdfs:comment` under `--metadata-profile rdfs`;
`see_also`, `source`, `license` and `conforms_to` give `rdfs:seeAlso`,
`dcterms:source`, `dcterms:license` and `dcterms:conformsTo`, and
`contributors` gives one `dcterms:contributor` IRI per contributor: their
GitHub account. `annotations` give the rest: `owl:versionInfo`,
`dcterms:creator` and `dcterms:identifier` as literals, and `owl:priorVersion`,
`prov:wasDerivedFrom`, `dcterms:references` and `dcterms:publisher` (ASCS e.V.,
`https://www.asc-s.de/`) as IRIs.

The latter four are declared by the **ontology-header profile**
(`linkml/ontology-header/`), a schema profile in LinkML's sense: its metaclass
`OntologyHeader` has one attribute per annotation, with the predicate as
`slot_uri`, range `nodeidentifier` and `implements: [owl:AnnotationProperty]`,
and marks the release and the publisher required. A domain imports the profile
and states `instantiates: [ontology-header:OntologyHeader]`; its annotations
then become IRIs on declared annotation properties, about which the OWL states
no logical axioms. The domains generate with `--no-mergeimports` and
`--exclude-imports`, so the metaclass stays in the profile: a domain's OWL has
`owl:imports` of the profile and types the ontology `ontology-header:OntologyHeader`,
and the profile's shapes check that header. What cannot be expressed is G16.

**M9 — Narrowing is stated where the value sits.** Every link is typed only
`manifest:Link` in the data, so a narrowing that depends on where the link
hangs is a `range_expression` on the owning property: `hasLicense` requires a
license category, `hasManifestReference` a manifest category, and envited-x
narrows the access role and category of every link it owns to its own enums.
The named classes (`ArtifactLink`, `LicenseLink`, `ManifestLink`,
`ExtendedLink`, `ManifestLinkReference`, …) state the same conditions as shapes
for data that types its links, and for the leaf domains, which reference them
by IRI.

**M10 — Declare the prefixes a schema's shapes use.** `xsd:` and, where
schema.org terms are constrained, `sdo:` (never `schema:` — LinkML's built-in
types bind it to `http://schema.org/`). Required under `--exclude-imports` (G13).

**M11 — Nested values: `range_expression`, or a typed node.** A class range
gives `sh:class`; it does not apply the range class's shape to the value. What
a nested value must satisfy is stated with `range_expression` on the slot,
which gen-shacl renders as `sh:node` over an anonymous shape. Otherwise the
range class's own shape applies through `sh:targetClass`, which reaches the
value only if it is typed — in the data, or by `rdfs:range` under the
validator's RDFS inference — and reports the violation on the nested node
alone. A violation inside a `range_expression` carries the SHACL engine's
generic message (G21).

**M12 — Open vocabularies of named individuals.** An open class (manifest's
`AccessRole`, `Category`) stays a class. Each domain declares its own
individuals as an enum with `implements: [owl:NamedIndividual]`: `meaning` is
the individual's IRI, `instantiates` the open class it belongs to. The enum
closes only its own class (`owl:oneOf`), so `sh:in` over it admits exactly that
domain's values while the open class keeps admitting everyone's. Narrowing to a
single value is a one-value enum.

**M13 — An exemption follows from the structure.** "A JSON-LD artifact link
needs an IRI, a note and its ontology conformance, except the manifest's
self-reference" is stated on the artifact properties (`hasArtifacts`,
`hasReferencedArtifacts`, `hasLicense`) and on `ArtifactLink`, as
`any_of: [none_of: [JSON-LD file metadata], {iri, note, shapesConformsTo required}]`.
The self-reference hangs from `hasManifestReference`, which does not carry the
condition. A violation of the class expression reports the `sh:or`, not a
sentence (G21).

**M14 — URI references held as data.** A file location that may be relative is
`UriReference`, a type derived from `string` with `uri: xsd:anyURI`: an
`xsd:anyURI` literal in the OWL, the context and the SHACL, never resolved
against a document base. A link to a resource is `uri`, an IRI node
(`--xsd-anyuri-as-iri` for gen-owl and gen-jsonld-context).

---

## Open decisions

**D5 — `xsd:anyURI` literal or IRI node.** `manifest:filePath` is a literal
(M14); `manifest:iri` and `sh:conformsTo` are IRI nodes. ositrace's
`validationReport` stays an `xsd:anyURI` literal, as in its instance data. A
repository-wide rule for which URI-valued properties are resources is open.

**D11 — Bare class terms in the envited-x context.** The renamed envited-x
classes (M4) lose their bare context terms (`Content`, `Format`, `Manifest`, …).
No instance uses a bare class name, and every instance expands to the same RDF.
`alias` exists for slots only, so this cannot be avoided (G10).

---

## Generator gaps

| | Gap | Consequence | Candidate fix |
|---|---|---|---|
| G3 | gen-shacl narrows slot-level `exactly_one_of` to the default range, silently | a `string` or `integer` choice rejects integers | render as `sh:xone` |
| G5 | `path_rule` and `inverse` are in the metamodel but not rendered by gen-shacl | constraints over property paths or incoming edges cannot be expressed; M13 states the one exemption that needed it structurally | render derived-slot paths as `sh:path` sequences / `sh:inversePath` |
| G6 | every class shape gets `sh:targetClass` | no target-less reusable shapes; a target no instance is typed with is inert | — |
| G8 | the metamodel has no exclusive numeric bounds | `manifest:width > 0` becomes `>= 0` at best; the dimensions are left unbounded | metamodel change; an inclusive bound plus a `none_of` exclusion states it in SHACL, but not in OWL (G19) |
| G10 | `alias` has `domain: slot_definition`; gen-jsonld-context ignores it on a class | a class cannot keep a context term that differs from its LinkML name (D11) | metamodel change |
| G12 | `types.yaml` documents `uri` as a literal "unless it is an identifier", while `rdflib_dumper` and `shaclgen` emit IRI nodes | the normative contract is unclear | documentation change in `types.yaml` stating the actual contract |
| G13 | with `--exclude-imports`, a prefix declared only in an imported schema is not expanded | a datatype or path CURIE such as `<xsd:float>` matches nothing; the build rejects unexpanded CURIEs | expand with the full closure's namespaces; schemas declare the prefixes their shapes use (M10) |
| G14 | rule converter: a rule without preconditions is skipped | "always" is written as a class expression instead (`has_member` in `all_of`) | translate unconditional postconditions |
| G15 | slot-level `equals_string` on an enum-ranged slot raises in gen-shacl, although a class-expression condition accepts it | a slot narrowed to one value uses a one-value enum (M12) | resolve the value as `_add_enum` does |
| G16 | `contributors` has the range `uriorcurie`, and the metamodel has no structured agent; native `license` and `conforms_to` are strings; under `--default-language en` every string annotation is language-tagged; the ontology's `rdfs:label` is the schema `name` (`title` becomes `dcterms:title`) | the header names contributors by IRI only (a `foaf:Person` node cannot be stated); `dcterms:license` and `dcterms:conformsTo` are literals; `owl:versionInfo` and `dcterms:identifier` carry `@en` | metamodel change for structured agents; leave non-linguistic annotations untagged |
| G17 | gen-owl describes every slot it emits, including one whose `slot_uri` belongs to another vocabulary | ontology-header gives `dcterms:publisher`, `owl:priorVersion`, … its own `rdfs:label`, `rdfs:comment` and `skos:inScheme`; manifest does so for `skos:note` and `sh:conformsTo` | describe a foreign predicate only where it is defined |
| G18 | gen-jsonld-context renders a `nodeidentifier` range as `"@type": "shex:nonLiteral"`, not `"@type": "@id"`, without declaring `shex` | a plain JSON string under one of the ontology-header context's terms becomes a typed literal; a `{"@id": …}` value is unaffected | map `nodeidentifier` to `@id` |
| G19 | gen-owl renders no presence or cardinality condition (`required`, `minimum_cardinality`) inside an anonymous class expression | `any_of` / `none_of` conditions such as M13 are weaker in the OWL than in the SHACL | emit `owl:someValuesFrom` / cardinality restrictions for slot conditions |
| G20 | the metamodel compares a slot with a constant, never with another slot | OpenLABEL `minValue` ≤ `maxValue` is not enforced; reversed bounds are accepted | a cross-slot comparison mapped to `sh:lessThanOrEquals` |
| G21 | `--message-template` gives `sh:message` to a class's property shapes only; the anonymous shapes of `range_expression` and boolean expressions carry none | such violations read "Value … not in list …" or "Node … must conform to …" instead of the slot's description | apply the template to anonymous property shapes; a boolean expression's `description` as its `sh:message` |
| G22 | the metamodel has no version IRI: gen-owl takes the schema `id` as the ontology IRI, and `owl:versionIRI` is not an annotation | an ontology series cannot have a permanent ontology IRI (`…/manifest`) with a version IRI per release, as OWL 2 §3.3, OBO FP-004 and FOOPS VER1 expect; the permanent identifier is the `dcterms:identifier` literal | a schema-level version IRI in the metamodel, emitted as `owl:versionIRI` |

---

## Repository findings outside LinkML

- **R1.** Per-resource inference (`_abox_inference`) applies rdfs3 to every
  non-literal object, blank nodes included, exactly as `apply_rdfs_inference`
  does. A unit test in `tests/unit/validators/shacl/test_inference.py` pins both
  paths to the same result.
- **R2.** Per-resource validation merges neither fixtures nor the
  ontology into the data graph. External references (did:web fixtures) are
  typed by `rdfs:range` and then validated without their data, and individuals
  declared in the OWL (`manifest:isLicense a manifest:LicenseCategory`) are
  invisible to `sh:class`. Committed valid instances of automotive-simulator,
  ositrace and manifest are rejected in `--per-resource` mode; the default
  merged mode accepts them.
- **R5.** manifest and envited-x each define `isManifest`, `isLicense`,
  `isMiscellaneous` and `isPublic` — two IRIs per concept.
- **R6.** Generated ontologies state no `owl:versionIRI` (M8). The registry,
  the docs build and the class pages use the ontology IRI as the version IRI;
  `registry_updater` logs a warning for each such ontology.

## Harness

`scripts/compare_artifacts.py` (`just verify-linkml <domain>`) compares a
candidate artifact set with the committed one. For a generated domain the
committed set is the generator's output, so it checks that the build reproduces
it; for a hand-written domain it measures a port before the switch.

Layers: `header` (ontology node), `vocab` (classes, properties, the class and
property hierarchies, `owl:equivalentClass` axioms, and no unexpanded IRI),
`context` (JSON-LD expansion of every test instance), `shacl` (verdict and
violations per test instance), `probe` (adversarial instances derived in RDF
space from every committed shape, judged by the violations a mutation *adds*).
The probes change or remove a constrained value, add a second value where at
most one is allowed, and remove an optional property, which must not add a
violation on either side. `--dependents` also runs the `shacl` and `probe`
layers on the test instances of every domain that imports the measured one, so
a constraint a domain inherits is measured on that domain's data.

The `shacl` and `probe` layers validate per resource, which shares the loaded
schemas across files but is affected by R2. Violations are compared as (focus
IRI, path, component); blank focus nodes are reduced to `_`, so a second
violation of the same path and component on another blank node is not
distinguished. The harness measures SHACL behaviour; it is not an OWL reasoner
and does not compare entailments.
