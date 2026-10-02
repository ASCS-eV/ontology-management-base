# LinkML migration — modelling decisions, gaps and open questions

The ontologies are re-modelled in LinkML by **intent**: each hand-written
construct is traced to what it was meant to express, and that intent is modelled
with the LinkML mechanism designed for it. The generators are the only thing
that runs — nothing is pre- or post-processed — so a construct LinkML cannot
express shows up as a measured gap, never as a patch.

Every entry below is verified against the generator source or with a minimal
schema.

## Status

`manifest`, `georeference`, `envited-x` and `ositrace` are generated from
`linkml/<domain>/<domain>.yaml` by `just generate` (through
`scripts/build_linkml_domain.sh` and `linkml/<domain>/gen-flags.env`); their
`artifacts/<domain>/` files are never edited by hand. The other domains are
hand-written and import them.

What the generated artifacts cannot state, per domain:

| Domain | Remaining |
|---|---|
| manifest | G8 (`width`, `height`, `depth` greater than 0); G16 |
| georeference | G16 |
| envited-x | D11 (bare class terms); G16 |
| ositrace | G16 |

The generators come from the ASCS-eV LinkML fork, pinned in `uv.lock`. Besides
upstream LinkML the models use these fork features: `--inlined-as-node`,
`has_member` as `sh:qualifiedValueShape`, `instantiates` on permissible values,
string-derived `xsd:anyURI` types as literals, IRI-valued metadata, class-level
boolean expressions and the rule-to-SPARQL converter.

---

## Modelling mechanisms

**M1 — Dependencies are imported, as CURIEs.** A class or property owned by
another ontology is never restated or stood in for locally; its schema is
imported. The import is written as a CURIE whose prefix plus local name is the
dependency's `id` (`envitedx_ontology:v4`), the idiom LinkML itself uses for
`linkml:types`. gen-owl then emits the correct `owl:imports` IRI, and
`--no-mergeimports` / `--exclude-imports` keep the dependency's own classes and
shapes out of the domain's artifacts. An absolute-IRI import is not usable for a
dependency that has relative imports of its own (G9).

**M2 — Specialisation is `is_a`, for classes and for slots.** Class `is_a`
yields `rdfs:subClassOf`; slot `is_a` yields `rdfs:subPropertyOf`
(`owlgen.py:1088`). `subproperty_of` is **not** the property hierarchy: the
metamodel defines it as a value set ("any ontological child … is a valid value
for the slot"), which is why gen-shacl renders it as `sh:in`. A super-property
whose sub-properties have different ranges takes the union of them as its own
range (`envited-x:hasResourceDescription`), and each class narrows it to its own
in `slot_usage`.

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

**M5 — Choices.** "Inline object or link" is slot-level `any_of` over the two
classes. "One of two profiles" and "at least one of" are class-level `any_of`
with `slot_conditions` — the complete statement of the intent, rendered by
gen-owl (`owl:unionOf`) and by gen-shacl (`sh:or` over the member shapes; a
member it cannot translate makes it skip the whole operator, and the build fails
on that).

**M6 — Conditional constraints are `rules`.** The rule converter
(`--emit-rules`, on by default) translates: conditional-required,
conditional-absent, presence-implies-value, exclusive-value, numeric-threshold
preconditions, one-hop nested preconditions (`range_expression.slot_conditions`)
and `has_member` postconditions — one postcondition per rule. A rule it cannot
translate is skipped, and the build fails on that (G2, G14).

**M7 — Closed value sets are enums.** Road types, lane types, OSI message types
and the like are standardised closed sets; an enum is correct and renders as
`sh:in`.

**M8 — Header from schema metadata.** `description` becomes `rdfs:comment`
under `--metadata-profile rdfs`; `see_also`, `source`, `license` and
`conforms_to` give `rdfs:seeAlso`, `dcterms:source`, `dcterms:license` and
`dcterms:conformsTo`, and `contributors` gives one `dcterms:contributor` IRI per
contributor: their GitHub account. `annotations` give the rest:
`owl:versionInfo`, `dcterms:creator` and `dcterms:identifier` as literals, and
`owl:versionIRI`, `owl:priorVersion`, `prov:wasDerivedFrom`,
`dcterms:references` and `dcterms:publisher` (ASCS e.V., `https://www.asc-s.de/`)
as IRIs, because those properties take resources. What cannot be expressed is
G16.

**M9 — Narrowing is a subclass, stated where the value sits.** "A license link
is a link whose category is a license category" is `LicenseLink is_a
ArtifactLink` with a narrowed slot, and the property the link hangs from takes
it as its range (`hasLicense`). Every link is typed only `manifest:Link` in the
data, so the narrowing applies through the range: the SHACL checks an inlined
value against its range class's shape (M11). envited-x narrows by property in
the same way: `ExtendedLink` for every ENVITED-X artifact link,
`ManifestLinkReference` for a linked manifest, `SimulationManifest` for a
simulation asset's manifest.

**M10 — Declare the prefixes a schema's shapes use.** `xsd:` and, where
schema.org terms are constrained, `sdo:` (never `schema:` — LinkML's built-in
types bind it to `http://schema.org/`). Required under `--exclude-imports` (G13).

**M11 — Inlined values by their shape, referenced individuals by their type.**
gen-shacl runs with `--inlined-as-node`: a value written inline (a link, its
file metadata, its dimensions, an inline manifest) is checked against its range
class's shape (`sh:node`), whatever type it states; a reference to a named
individual (an access role, a category) keeps `sh:class`. A value is inlined
when its slot says `inlined` / `inlined_as_list` or its range class has no
identifier, so the classes of named individuals carry an identifier slot
(`manifest:AccessRole`, `manifest:Category`). A class shape also requires its
parents' and mixins' shapes, so their rules and class expressions apply to a
value reached through `sh:node`.

**M12 — Open vocabularies of named individuals.** An open class (manifest's
`AccessRole`, `Category`) stays a class. Each domain declares its own
individuals as an enum with `implements: [owl:NamedIndividual]`: `meaning` is
the individual's IRI, `instantiates` the open class it belongs to. The enum
closes only its own class (`owl:oneOf`), so `sh:in` over it admits exactly that
domain's values while the open class keeps admitting everyone's. Narrowing to a
single value is a one-value enum.

**M13 — An exemption is a class of its own.** "A JSON-LD artifact link needs an
IRI, a note and its ontology conformance, except the manifest's self-reference"
is a rule on `ArtifactLink`, the range of every artifact property, while the
self-reference is a `ManifestLink`, which is not an artifact link. The
exemption follows from the structure, not from an incoming edge (G5).

**M14 — URI references held as data.** A file location that may be relative is
`UriReference`, a type derived from `string` with `uri: xsd:anyURI`: an
`xsd:anyURI` literal in the OWL, the context and the SHACL, never resolved
against a document base. A link to a resource is `uri`, an IRI node
(`--xsd-anyuri-as-iri` for gen-owl and gen-jsonld-context).

---

## Open decisions

**D11 — Bare class terms in the envited-x context.** The renamed envited-x
classes (M4) lose their bare context terms (`Content`, `Format`, `Manifest`, …).
No instance uses a bare class name, and every instance expands to the same RDF.
`alias` exists for slots only, so this cannot be avoided (G10).

---

## Generator gaps

| | Gap | Consequence | Candidate fix |
|---|---|---|---|
| G2 | rule converter: `value_presence: ABSENT` is not supported as a *precondition*; skipped at DEBUG | "no channels ⇒ `formatType` required" cannot be written as a rule | extend the converter |
| G3 | gen-shacl narrows slot-level `exactly_one_of` to the default range, silently | a `string` or `integer` choice rejects integers | render as `sh:xone` |
| G5 | `path_rule` and `inverse` are in the metamodel but not rendered | constraints over property paths or incoming edges cannot be expressed; M13 states the one exemption that needed it structurally | render derived-slot paths as `sh:path` sequences / `sh:inversePath` |
| G6 | every class shape gets `sh:targetClass` | no target-less reusable shapes; a target no instance is typed with is inert, and the shapes are reached through `sh:node` (M11) | — |
| G7 | in class-URI naming mode a class range is `sh:class` unless `--inlined-as-node` makes an inlined one `sh:node`; `--use-native-names` gives `sh:node` for every class range, references included, and names shapes after LinkML names | the build uses `--inlined-as-node` (M11) | — |
| G8 | the metamodel has no exclusive numeric bounds | `manifest:width > 0` becomes `>= 0` at best; the dimensions are left unbounded | metamodel change |
| G9 | linkml_runtime resolves a dependency's relative imports against its IRI with `os.path.normpath`, collapsing `https://` to `https:/` | no schema with relative imports can be imported by absolute IRI; M1 avoids it | use `urljoin` in `imports_closure` |
| G10 | `alias` has `domain: slot_definition` | a class cannot keep a context term that differs from its LinkML name (D11) | metamodel change |
| G12 | `types.yaml` documents `uri` as a literal "unless it is an identifier", while `rdflib_dumper` and `shaclgen` emit IRI nodes | the normative contract is unclear | documentation change in `types.yaml` stating the actual contract |
| G13 | with `--exclude-imports`, gen-shacl no longer knows prefixes declared only in imported schemas: datatype and path CURIEs from `linkml:types` (`xsd:`) or Gaia-X (`sdo:`) are emitted unexpanded, e.g. `sh:datatype <xsd:float>`, which no value matches | silently rejects every value of those slots | expand with the full closure's namespaces; schemas declare the prefixes their shapes use (`xsd:`, `sdo:`) |
| G14 | rule converter: a rule without preconditions is skipped | "always" is written as a class expression instead (`has_member` in `all_of`) | translate unconditional postconditions |
| G15 | slot-level `equals_string` on an enum-ranged slot raises in gen-shacl, although a class-expression condition accepts it | a slot narrowed to one value uses a one-value enum (M12) | resolve the value as `_add_enum` does |
| G16 | `contributors` has the range `uriorcurie`, and the metamodel has no structured agent; under `--default-language en` every string annotation is language-tagged; the ontology's `rdfs:label` is the schema `name` (`title` becomes `dcterms:title`) | the header names contributors by IRI only, without name or organisation (a `foaf:Person` node cannot be stated); `owl:versionInfo` and `dcterms:identifier` carry `@en` | metamodel change for structured agents; leave non-linguistic annotations untagged |

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
- **R4.** `artifacts/openlabel-v2/` is generated without
  `--no-use-native-uris`, so its OWL declares `openlabel_v2:QuantitativeValue`,
  `openlabel_v2:minValue` and `openlabel_v2:maxValue` while its SHACL uses
  `schema:QuantitativeValue` (16×), `schema:minValue` and `schema:maxValue`.
- **R5.** manifest and envited-x each define `isManifest`, `isLicense`,
  `isMiscellaneous` and `isPublic` — two IRIs per concept.

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
distinguished.
