# OpenLabel v2 — Gap Analysis

Comprehensive comparison between the handcrafted v1 ontology
(`artifacts/openlabel/`) and the LinkML-generated v2 ontology
(`artifacts/openlabel-v2/`). The v2 schema source is
`linkml/openlabel-v2/openlabel-v2.yaml`.

---

## 1. Structural overview

| Aspect | v1 (handcrafted) | v2 (LinkML-generated) |
|--------|-------------------|-----------------------|
| **OWL classes** | 243 (`rdfs:Class`, deep hierarchy) | 176 (`owl:Class`, flat + enum individuals) |
| **OWL properties** | 0 explicit (implicit via class hierarchy) | 112 (32 `owl:ObjectProperty` + 80 `owl:DatatypeProperty`) |
| **Annotations** | 275 `rdfs:label@en`, 271 `rdfs:comment@en` | 281 `rdfs:label@en`, 288 `skos:definition@en` |
| **Enum representation** | `rdfs:Class` subclass trees | 27 `EnumDefinition` → 144 permissible values |
| **SHACL shapes** | 6 `sh:NodeShape`, 108 `sh:property`, 18 `sh:sparql` | 7 `sh:NodeShape`, 113 `sh:property`, 17 `sh:sparql` |
| **SHACL annotations** | `sh:name@en` + `sh:description@en` + `sh:message@en` | `sh:description@en` + `sh:message@en` |
| **SHACL cardinality** | 2 `sh:minCount 1` + 4 `sh:minCount 0` (no-ops), 0 `sh:maxCount` | 2 `sh:minCount 1`, 109 `sh:maxCount 1` |
| **SHACL closed shapes** | 0 | 7 (`sh:closed true`) |
| **SHACL union types** | 0 `sh:or` | 8 `sh:or` (literal OR QuantitativeValue, enum union) |
| **Context terms** | 113 (no `@vocab` coercion) | 121 top-level + 81 nested (27 with `@type: @vocab` scoped context) |
| **Schema classes** | — | 7 structural classes |
| **Schema slots** | — | 112 (39 boolean, 2 integer, 6 `any_of`, 29 enum, rest string/decimal) |
| **Schema rules** | — | 17 conditional constraints (LinkML rules) |
| **Test data** | 1 valid + 3 invalid instances | 1 valid + 4 invalid instances |

### 1.1 Class hierarchy

v1 uses a three-level class hierarchy:

```
Tag (root)
├── AdminTag
├── Odd (61 sh:property)
│   ├── category classes (OddEnvironment, OddScenery, …)
│   │   └── enum families (DrivableAreaType, SceneryFixedStructure, …)
│   │       └── leaf values (RoadTypeMotorway, FixedStructureBuilding, …)
│   └── boolean flag classes (MotionAccelerate, WeatherRain, …)
├── Behaviour (24 sh:property)
│   └── BehaviourCommunication, ConnectivityCommunication, …
├── RoadUser (4 sh:property)
│   └── RoadUserHuman, RoadUserVehicle
└── QuantitativeValue (2 sh:property)
```

v2 has 7 flat structural classes:

```
Tag, AdminTag, Odd, Behaviour, RoadUser, QuantitativeValue, Scenario
```

All enum values are `owl:NamedIndividual` instances — no intermediate
category classes.

### 1.2 Enum families comparison

All 27 v2 enums map to v1 class-based enum families. Value counts match
exactly for all enums. The v2 enums are:

| v2 Enum | Values | v1 equivalent |
|---------|--------|---------------|
| `BehaviourCommunicationEnum` | 8 | `BehaviourCommunication` subclasses |
| `ConnectivityCommunicationEnum` | 8 | `ConnectivityCommunication` subclasses |
| `ConnectivityPositioningEnum` | 3 | `ConnectivityPositioning` subclasses |
| `DaySunPositionEnum` | 4 | `DaySunPosition` subclasses |
| `DrivableAreaEdgeEnum` | 6 | `DrivableAreaEdge` subclasses |
| `DrivableAreaSurfaceConditionEnum` | 7 | `DrivableAreaSurfaceCondition` subclasses |
| `DrivableAreaSurfaceFeatureEnum` | 4 | `DrivableAreaSurfaceFeature` subclasses |
| `DrivableAreaSurfaceTypeEnum` | 3 | `DrivableAreaSurfaceType` subclasses |
| `DrivableAreaTypeEnum` | 9 | `DrivableAreaType` subclasses |
| `EnvironmentParticulatesEnum` | 5 | `EnvironmentParticulates` subclasses |
| `GeometryTransverseEnum` | 5 | `GeometryTransverse` subclasses |
| `IlluminationArtificialEnum` | 2 | `IlluminationArtificial` subclasses |
| `IlluminationLowLightEnum` | 2 | `IlluminationLowLight` subclasses |
| `JunctionIntersectionEnum` | 5 | `JunctionIntersection` subclasses |
| `JunctionRoundaboutEnum` | 10 | `JunctionRoundabout` subclasses |
| `LaneSpecificationTravelDirectionEnum` | 2 | `LaneSpecificationTravelDirection` subclasses |
| `LaneSpecificationTypeEnum` | 6 | `LaneSpecificationType` subclasses |
| `RainTypeEnum` | 3 | `RainType` subclasses |
| `RoadUserHumanEnum` | 7 | `RoadUserHuman` subclasses |
| `RoadUserVehicleEnum` | 11 | `RoadUserVehicle` subclasses |
| `SceneryFixedStructureEnum` | 4 | `SceneryFixedStructure` subclasses |
| `ScenerySpecialStructureEnum` | 6 | `ScenerySpecialStructure` subclasses |
| `SceneryTemporaryStructureEnum` | 4 | `SceneryTemporaryStructure` subclasses |
| `SceneryZoneEnum` | 5 | `SceneryZone` subclasses |
| `SignsInformationEnum` | 4 | `SignsInformation` subclasses |
| `SignsRegulatoryEnum` | 4 | `SignsRegulatory` subclasses |
| `SignsWarningEnum` | 5 | `SignsWarning` subclasses |
| **Total** | **142** | **142 leaf classes** |

### 1.3 Boolean flag slots

v1 models 43 boolean flags as `rdfs:Class` instances (e.g.,
`MotionAccelerate`, `WeatherRain`, `SubjectVehicleSpeed`). These appear
as leaf classes under Odd/Behaviour shapes. v2 models them as explicit
`boolean`-range slots. The boolean flags are not enum values and are
correctly excluded from the enum comparison.

---

## 2. Functional gaps (limitations)

### L1. Conditional constraints — ✅ RESOLVED

v1 SHACL uses 17 `sh:sparql` rules enforcing: *"if boolean flag is absent
or false, the corresponding value must not be present"*. All 17 flag↔value
pairs are now modeled as LinkML `rules:` with `value_presence` /
`equals_string` postconditions on the `Odd` and `Behaviour` classes. A
further v1 SPARQL rule enforces `minValue ≤ maxValue` on `QuantitativeValue`.

**Schema status:** ✅ 17 rules defined in `openlabel-v2.yaml` (flag↔value).
The `minValue ≤ maxValue` constraint uses LinkML `minimum_value` on
individual slots instead of a cross-field SPARQL rule.

**SHACL status:** ✅ `gen-shacl --emit-rules` now generates `sh:sparql`
constraints from LinkML `rules:` blocks. Implemented in ASCS-eV/linkml fork
(`feat/shaclgen-rules-sparql`) and cherry-picked to develop. Upstream PR
pending ([linkml/linkml#2464](https://github.com/linkml/linkml/issues/2464)).

**Coverage:** 17/17 boolean-guard constraints generated (100% of Pattern A).
The Pattern B cross-field comparison (1 constraint) is not generated because
it is not modeled as a LinkML rule; it is handled via slot-level `minimum_value`
constraints instead.

**Impact:** Data with a value but no corresponding flag=true will pass v2
SHACL validation but would fail v1. The constraints *are* enforceable via
`linkml-validate` (JSON Schema path).

### L2. `trafficAgentTypeValue` — Resolved

v1 defines `trafficAgentTypeValue` (domain: `TrafficAgentType`, range:
`RoadUser`). This property links a traffic agent type classification to
specific road user types. Refer to BSI PAS-1883 Section 5.4.a.4.

**Schema status:** ✅ Modeled as `TrafficAgentType` boolean flag +
`trafficAgentTypeValue` multivalued slot with `any_of:
[RoadUserHumanEnum, RoadUserVehicleEnum]`. Conditional rule enforces
flag=true when value is present.

**Design note:** v1's `range: <RoadUser>` (class reference) was adapted
to enum-based validation in v2, referencing the existing `RoadUserHuman`
and `RoadUserVehicle` enum families. This maintains the semantic intent
(which road user types are present in traffic) while fitting v2's flat
property-based architecture.

### L3. `any_of` union ranges produce OWL warnings

6 v2 slots use `any_of` to allow both a literal (e.g., `decimal`) and an
object (e.g., `QuantitativeValue`):

- `motionAccelerateValue`, `subjectVehicleSpeedValue`,
  `trafficAgentDensityValue`, `trafficFlowRateValue`,
  `trafficSpecialVehicleValue`, `trafficVolumeValue`

`gen-owl` produces "Multiple owl types" warnings because these combine
`rdfs:Literal` and `owl:Thing`. The generated OWL uses
`owl:unionOf` but some reasoners may not handle mixed literal/object
unions. v1 avoids this by using only `QuantitativeValue` as the range.

**Schema status:** ✅ Intentional — allows simpler data (plain number) or
richer data (with unit/bounds).

**Impact:** Minor — the union semantics are partially lost in some OWL
tools, but SHACL validation works correctly.

### L4. Intermediate category classes absent in v2

v1 organizes enum families under intermediate grouping classes:
`OddEnvironment`, `OddScenery`, `OddDynamicElements`,
`DrivableAreaGeometry`, `DynamicElementsSubjectVehicle`,
`DynamicElementsTraffic`, etc. (64 total parent/category classes).

v2 uses flat enum definitions — no intermediate hierarchy. This is
intentional (LinkML enums are flat lists), but means v1 queries or
reasoning that depend on the intermediate classification structure will
not work identically in v2.

**Schema status:** ✅ Intentional simplification.

**Impact:** No effect on SHACL validation. May affect SPARQL queries or
OWL reasoning that traverse the class hierarchy.

---

## 3. Improvements in v2 over v1

### I1. Typed properties instead of flat `rdfs:Property`

v1 declares all 33 properties as `rdfs:Property` without distinguishing
object properties from datatype properties. v2 generates 32
`owl:ObjectProperty` and 78 `owl:DatatypeProperty` with explicit domains
and ranges. This enables better tooling support and reasoning.

### I2. Explicit enum validation via `@type: @vocab` context

v2 context uses `@type: @vocab` with scoped `@context` for all 27 enum
slots (via the ASCS-eV LinkML fork). This allows bare string values
(e.g., `"RoadTypeMotorway"`) to expand to full IRIs during JSON-LD
processing. v1 context requires prefixed compact IRIs
(`"openlabel:RoadTypeMotorway"`).

### I3. Additional structural class: `Scenario`

v2 adds a `Scenario` class that groups `Tag` instances (with multiplicity
constraints). v1 uses `Scenario` as a leaf class under `Tag`. This
enables validation of complete scenario descriptions as a unit.

### I4. `QuantitativeValue` with bounds properties

v2 extends `QuantitativeValue` with `cmns-q:hasLowerBound` and
`cmns-q:hasUpperBound` from Commons Ontology in addition to
`schema:minValue`/`schema:maxValue`. This aligns with formal measurement
ontologies.

### I5. Normalized prefixes

v2 uses well-known prefix names (`schema:` instead of `sdo:`, standard
namespace IRIs) via the `--normalize-prefixes` generator flag.

### I6. Deterministic serialization

v2 OWL output uses RDFC-1.0 canonical serialization
(`--deterministic` flag), producing reproducible byte-identical output
across regeneration runs.

---

## 4. Cosmetic differences (intentional, not limitations)

These are deliberate improvements or generator-default behaviors:

- **`@en` language tags** — gen-owl and gen-shacl emit language-tagged
  literals via `--default-language en`, matching v1's `@en` annotations.
- **`sh:name`/`sh:description`/`sh:message`** — gen-shacl emits `sh:name`
  (slot title), `sh:description` (slot description), and `sh:message`
  (configurable via `--message-template` with `{name}`, `{title}`,
  `{description}`, `{class}`, `{path}` placeholders). v1 used manually
  written `sh:message` values; v2 generates them consistently from schema
  metadata.
- **`sh:class` instead of `sh:node`** — functionally equivalent; `sh:class`
  is arguably more correct (checks `rdf:type` rather than shape conformance).
- **`sh:order` numbering** — v1 uses manually assigned order values; v2
  uses sequential generator-assigned values.

---

## 5. Test data comparison

| Aspect | v1 | v2 |
|--------|----|----|
| Valid instances | 1 (`openlabel_instance.json`) | 1 (`openlabel-v2_instance.json`) |
| Invalid instances | 3 (wrong value, decimal for integer, string for boolean) | 4 (wrong value, decimal for integer, string for boolean, wrong literal types) |
| Enum value format | Prefixed IRIs (`openlabel:RoadTypeMotorway`) | Bare strings (`RoadTypeMotorway`) via `@type: @vocab` |
| `.expected` files | ✅ All 3 present | ✅ All 4 present |

---

## 6. Summary of action items

### Resolved

| Item | Resolution |
|------|------------|
| `@en` language tags | ✅ `--default-language en` on gen-owl and gen-shacl |
| `sh:name`/`sh:message` | ✅ `--message-template "{name} ({class}): {description}"` |
| Enum `@type: @vocab` context | ✅ Fork feature `feat/contextgen-enum-vocab-coercion` |
| `--xsd-anyuri-as-iri` on gen-owl | ✅ Added to Makefile (was only on gen-jsonld-context) |
| Normalized prefixes | ✅ `--normalize-prefixes` on all generators |
| Deterministic serialization | ✅ `--deterministic` on all generators |
| L2: `trafficAgentTypeValue` | ✅ Boolean flag + multivalued enum slot (RoadUserHuman/Vehicle) with conditional rule |
| L5: `sh:minCount` required fields | ✅ Already correct — `minValue`/`maxValue` have `required: true`; 4 v1 `minCount 0` are no-ops |
| L6: Enum array support | ✅ 3 slots already `multivalued: true`; test data updated to use arrays |

### Remaining

| Priority | Item | Status |
|----------|------|--------|
| 🔴 High | L1: SHACL conditional constraints (18 `sh:sparql` rules) | Blocked on [linkml/linkml#2464](https://github.com/linkml/linkml/issues/2464) — 17 rules modeled in schema but `gen-shacl` ignores them |
| 🟢 Low | L3: `any_of` OWL warnings | Cosmetic; SHACL `sh:or` works correctly |
| ⚪ Info | L4: No intermediate category classes | Intentional; 29 grouping + 39 leaf→property = all 68 "missing" classes accounted for |
| ⚪ Info | L7: `rdfs:Class` vs `owl:Class` | v2 uses proper OWL vocabulary — more correct than v1 |
