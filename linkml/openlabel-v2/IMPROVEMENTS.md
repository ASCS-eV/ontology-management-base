# OpenLabel v2 Improvements over v1

This document lists the intentional improvements that the LinkML-modeled v2
makes over the handcrafted v1 artifacts. These are not gaps to close — they
are design decisions that make v2 better.

## Single Source of Truth

v1 was assembled from three independent sources:

- **OWL** — downloaded from ASAM, defines the class taxonomy
- **SHACL** — handcrafted by a third party, independently of the OWL
- **JSON-LD context** — auto-generated from OWL+SHACL by `context_generator.py`

This led to inconsistencies (see GAP_ANALYSIS.md §F1–F6). In v2, a single
LinkML schema generates all three artifacts coherently. OWL, SHACL, and
context are always in sync by construction.

## More Precise OWL Typing

| Aspect | v1 | v2 |
|--------|----|----|
| Class type | `rdfs:Class` | `owl:Class` |
| Property type | `rdfs:Property` | `owl:DatatypeProperty` / `owl:ObjectProperty` |

`owl:Class` and typed properties are valid OWL 2 and carry more semantic
information. Tools can distinguish data properties from object properties.

## More Precise Datatype Ranges

| Property group | v1 range | v2 range |
|----------------|----------|----------|
| Admin strings | `rdfs:Literal` | `xsd:string` |
| `scenarioCreatedDate` | `rdfs:Literal` | `xsd:dateTime` |
| Decimal measurements | `xsd:decimal` | `xsd:decimal` (unchanged) |
| Integer counts | `xsd:integer` | `xsd:integer` with `minimum_value` (unchanged) |

`xsd:string` and `xsd:dateTime` are concrete datatypes that enable proper
validation and type coercion, unlike the generic `rdfs:Literal`.

## Consistent Enum Modeling

v1 SHACL inconsistently modeled structurally identical OWL patterns:

| Property | v1 OWL | v1 SHACL (bug) | v2 (fixed) |
|----------|--------|----------------|------------|
| `RoadUserVehicle` | 11 subclasses | ✅ `sh:in` with 10 values | `sh:in` with 11 values |
| `RoadUserHuman` | 7 subclasses | ❌ `xsd:boolean` | `sh:in` with 7 values |
| `DaySunPosition` | 4 subclasses | ❌ `xsd:boolean` | `sh:in` with 4 values |

Both v1 SHACL (F1, F3) and v2 now correctly model these as enums.

## Expanded Enum Values

v2 adds enum values that exist in the v1 OWL but were omitted from v1 SHACL:

| Enum | Added values | Source |
|------|--------------|--------|
| `RoadUserVehicleEnum` | `VehicleAgricultural` | v1 OWL defines 11 subtypes, SHACL had 10 |
| `DrivableAreaTypeEnum` | `MotorwayManaged`, `MotorwayUnmanaged` | v1 OWL subtypes of `RoadTypeMotorway` |
| `ConnectivityCommunicationEnum` | `V2vCellular`, `V2vSatellite`, `V2vWifi`, `V2iCellular`, `V2iSatellite`, `V2iWifi` | v1 OWL subtypes of V2v/V2i |

## Missing Properties Restored

| Property | Description | Status in v1 |
|----------|-------------|--------------|
| `longitudinalUpSlopeValue` | Gradient (%) for up-slopes | OWL: ✅, SHACL: missing property (only SPARQL ref) |
| `particulatesWaterValue` | MOR in meters | OWL: ✅, SHACL: completely absent |

Both are now in the v2 schema and also fixed in v1 SHACL (F6).

## Cardinality Constraints

v2 adds `sh:maxCount 1` on all single-valued properties. v1 has no cardinality
constraints, allowing multiple values where only one is semantically valid.

## Closed Shapes

v2 generates `sh:closed true` with `sh:ignoredProperties (rdf:type)`. This
prevents instance data from containing undeclared properties that would
silently pass validation in v1's open shapes.

> **Note:** This is stricter than v1. Data with extra properties will fail v2
> validation. This is intentional — unknown properties should be explicitly
> rejected rather than silently ignored.

## New ASCS-eV Namespace

v1 uses the ASAM namespace (`https://openlabel.asam.net/V1-0-0/ontologies/`).
v2 uses the ASCS-eV namespace (`https://w3id.org/ascs-ev/envited-x/openlabel/v2/`),
following the project-wide migration from Gaia-X4PLC-AAD to ASCS-eV IRIs.

This enables independent evolution of the ontology outside of ASAM, with the
intent to contribute improvements back to an ASAM working group.

## Flat, Pragmatic Class Hierarchy

v1 OWL has ~25 intermediate grouping classes (`OddEnvironment`, `OddScenery`,
`BehaviourMotion`, `DrivableAreaGeometry`, etc.) that the v1 SHACL completely
ignores — all properties are validated directly on the 5 main shapes.

v2 omits these intermediate nodes entirely. The flat model is cleaner, matches
how SHACL actually works, and avoids the misleading `rdfs:domain` assertions
on leaf classes (e.g., `weatherWindValue` with domain `WeatherWind` when SHACL
validates it on `OddShape`).

## QuantitativeValue as a Proper Class

v1 defines `QuantitativeValueShape` in SHACL but `schema:QuantitativeValue` is
not declared in the OWL ontology. v2 properly declares `QuantitativeValue` as
a class with `minValue` and `maxValue` slots, visible in both OWL and SHACL.
