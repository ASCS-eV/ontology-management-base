# OpenLabel v1 → v2 Gap Analysis

This document records the differences between the handcrafted v1 artifacts
(`artifacts/openlabel/`) and the LinkML-generated v2 artifacts
(`artifacts/openlabel-v2/`). Each gap is classified and a resolution is given.

## Classification Legend

| Label | Meaning |
|-------|---------|
| ✅ RESOLVED | Fixed in the LinkML schema |
| ⚠️ V1 ERROR | Modeling inconsistency in v1 — intentionally not reproduced |
| 🔧 LIMITATION | Inherent to LinkML generators — accepted, no post-processing |

---

## ✅ RESOLVED — Schema fixes applied

### A1. Missing `longitudinalUpSlopeValue` slot

v1 OWL and SHACL both define `longitudinalUpSlopeValue` (gradient %) on
`LongitudinalUpSlope`. The v2 schema had `LongitudinalUpSlope` (boolean) and
`longitudinalDownSlopeValue` but was missing the up-slope value.

**Fix:** Add `longitudinalUpSlopeValue` slot (range `decimal`) to the `Odd`
class.

### A2. Missing `VehicleAgricultural` enum value

v1 OWL defines `VehicleAgricultural` as a subclass of `RoadUserVehicle`. It was
missing from the v2 `RoadUserVehicleEnum`.

**Fix:** Add `VehicleAgricultural` to `RoadUserVehicleEnum`.

### A3. Missing `particulatesWaterValue` slot

v1 OWL defines `particulatesWaterValue` (Meteorological Optical Range in meters)
on `ParticulatesWater`. It has no corresponding v1 SHACL constraint (OWL-only),
but is added for completeness.

**Fix:** Add `particulatesWaterValue` slot (range `decimal`) to the `Odd` class.

### A4. `scenarioCreatedDate` type precision

v1 OWL uses `xsd:dateTime`; v2 had `string`.

**Fix:** Change range to `datetime`.

### A5. `owl:versionIRI` metadata

v1 OWL includes `owl:versionIRI`. Ensure the LinkML schema `version` field
propagates to the generated OWL.

---

## ⚠️ V1 OWL↔SHACL INCONSISTENCIES

The v1 OWL ontology and v1 SHACL shapes were authored independently by
different parties. The OWL carries rich taxonomic subtypes, but the SHACL
author did not model many of them — reducing structured enums to booleans
or ignoring leaf classes. LinkML as a single source of truth resolves this:
the model generates both OWL and SHACL coherently.

Items are classified as either **UPGRADE** (fix the SHACL oversight by
modelling the OWL's semantic intent) or **OMIT** (genuinely not useful).

### B1. ~25 intermediate hierarchy classes — OMIT

Classes like `OddEnvironment`, `OddScenery`, `BehaviourMotion`,
`DrivableAreaGeometry`, `GeometryHorizontal`, `GeometryLongitudinal`,
`DrivableAreaLaneSpecification`, `DrivableAreaSigns`, `DrivableAreaSurface`,
`SceneryJunction`, `EnvironmentWeather`, `EnvironmentIllumination`,
`EnvironmentConnectivity`, `DynamicElementsTraffic`,
`DynamicElementsSubjectVehicle`, `OddDynamicElements`, `IlluminationDay`, etc.

These are pure OWL taxonomy grouping nodes. The v1 SHACL shapes bypass them
entirely — `OddShape` references leaf properties directly. They add hierarchy
complexity with zero validation value. The flat model is cleaner.

### B2. `RoadUserHuman` — UPGRADE boolean → enum

v1 OWL defines 7 subtypes of `RoadUserHuman` (AnimalRider, Cyclist, Driver,
Motorcyclist, Passenger, Pedestrian, WheelchairUser), structurally identical
to how `RoadUserVehicle` has 11 subtypes. The v1 SHACL correctly models
`RoadUserVehicle` as `sh:in` with IRI values, but inconsistently reduces
`RoadUserHuman` to `xsd:boolean`.

**v2 fix:** Model `RoadUserHuman` as an enum (`RoadUserHumanEnum`) with the
7 human subtypes, matching the pattern already used for `RoadUserVehicle`.

### B3. `DaySunPosition` — UPGRADE boolean → enum

v1 OWL defines 4 subtypes (`SunPositionFront`, `SunPositionLeft`,
`SunPositionRight`, `SunPositionBehind`). The SHACL treats it as `xsd:boolean`,
losing the directional information.

**v2 fix:** Model `DaySunPosition` as an enum (`DaySunPositionEnum`) with
the 4 directional values.

### B4. `DrivableAreaType` — UPGRADE add motorway subtypes

v1 OWL defines `MotorwayManaged` and `MotorwayUnmanaged` as subtypes of
`RoadTypeMotorway`. The SHACL `sh:in` list includes only `RoadTypeMotorway`,
making the managed/unmanaged distinction unreachable.

**v2 fix:** Replace `RoadTypeMotorway` with `RoadTypeMotorwayManaged` and
`RoadTypeMotorwayUnmanaged` in `DrivableAreaTypeEnum` (or add them alongside
the parent if both levels are useful).

### B5. `ConnectivityCommunication` — UPGRADE add technology subtypes

v1 OWL defines 3 subtypes each for `CommunicationV2v` (Cellular, Satellite,
Wifi) and `CommunicationV2i` (Cellular, Satellite, Wifi). The SHACL uses only
the parent classes `CommunicationV2v`/`CommunicationV2i`.

**v2 fix:** Expand `ConnectivityCommunicationEnum` with the 6 technology-
specific values, making the communication technology selectable in data.

### B6. `trafficAgentTypeValue` property — OMIT (for now)

Exists in v1 OWL (domain: `TrafficAgentType`, range: `RoadUser`) but has no
SHACL constraint. Semantically it links traffic metrics to a road user type,
but no validation existed. Could be added in a future iteration if a use case
emerges.

### B7. `rdfs:domain` pointing to leaf classes — FIXED BY DESIGN

v1 OWL defines properties like `weatherWindValue` with
`rdfs:domain <WeatherWind>` (a leaf class in the hierarchy). But v1 SHACL
places these properties on `OddShape`, not on a `WeatherWindShape`. The domain
assertion contradicts actual usage. In v2, slots are declared on the correct
parent class (`Odd`, `Behaviour`, `RoadUser`) — model and SHACL agree.

---

## 🔨 V1 SHACL FIXES — applied to `artifacts/openlabel/openlabel.shacl.ttl`

Since the v1 SHACL was authored independently of the OWL ontology, several
constraints are inconsistent with what the OWL defines. These are fixed
directly in the v1 SHACL to align it with the OWL as source of truth.

### F1. `RoadUserHuman` boolean → enum

The OWL defines 7 subclasses of `RoadUserHuman`, structurally identical to
`RoadUserVehicle` (which the SHACL correctly models as `sh:in`). The SHACL
inconsistently used `xsd:boolean`.

**Fix:** Replace `sh:datatype xsd:boolean` with `sh:in` containing 7 IRIs:
`HumanAnimalRider`, `HumanCyclist`, `HumanDriver`, `HumanMotorcyclist`,
`HumanPassenger`, `HumanPedestrian`, `HumanWheelchairUser`.

### F2. `RoadUserVehicle` missing `VehicleAgricultural`

The OWL defines 11 vehicle subclasses including `VehicleAgricultural`. The
SHACL `sh:in` list has only 10 values.

**Fix:** Add `openlabel:VehicleAgricultural` to the `sh:in` list.

### F3. `DaySunPosition` boolean → enum

The OWL defines 4 subclasses (`SunPositionFront`, `SunPositionLeft`,
`SunPositionRight`, `SunPositionBehind`). The SHACL used `xsd:boolean`,
discarding the directional information.

**Fix:** Replace `sh:datatype xsd:boolean` with `sh:in` containing 4 IRIs.

### F4. `DrivableAreaType` missing motorway subtypes

The OWL defines `MotorwayManaged` and `MotorwayUnmanaged` as subclasses of
`RoadTypeMotorway`. The SHACL only includes the parent.

**Fix:** Add `openlabel:MotorwayManaged` and `openlabel:MotorwayUnmanaged`
to the `sh:in` list (alongside `RoadTypeMotorway` for backward compatibility).

### F5. `ConnectivityCommunication` missing technology subtypes

The OWL defines 3 subtypes each for V2V and V2I communication (Cellular,
Satellite, Wifi). The SHACL only includes the parent classes.

**Fix:** Add `openlabel:V2vCellular`, `openlabel:V2vSatellite`,
`openlabel:V2vWifi`, `openlabel:V2iCellular`, `openlabel:V2iSatellite`,
`openlabel:V2iWifi` to the `sh:in` list (alongside parents).

### F6. Missing `particulatesWaterValue` constraint

The OWL defines `particulatesWaterValue` (MOR in meters, `xsd:decimal`) on
`ParticulatesWater`. The SHACL has no constraint for it despite validating
all other `*Value` properties.

**Fix:** Add `sh:property` for `openlabel:particulatesWaterValue` with
`sh:datatype xsd:decimal` to `OddShape`.

---

## 🔧 LIMITATIONS — LinkML generator constraints, accepted

These are inherent differences between handcrafted v1 artifacts and what LinkML
generators produce. Per project rules, no pre/post-processing is applied.

### C1. OWL class/property types

| Aspect | v1 | v2 (LinkML) |
|--------|----|----|
| Class type | `rdfs:Class` | `owl:Class` |
| Property type | `rdfs:Property` | `owl:DatatypeProperty` / `owl:ObjectProperty` |

**Impact:** None. `owl:Class` and typed properties are valid OWL2 and more
semantically precise. This is an improvement.

### C2. ~~No `sh:or` for QuantitativeValue ranges~~ ✅ RESOLVED

v1 SHACL uses `sh:or` on 6 properties to accept **either** a scalar
(`xsd:decimal`) **or** a `schema:QuantitativeValue` range:

- `motionAccelerateValue`, `motionDecelerateValue`, `motionDriveValue`
- `subjectVehicleSpeedValue`, `laneSpecificationDimensionsValue`,
  `laneSpecificationLaneCountValue`

**Resolution:** LinkML v1.10.0 supports `any_of` → `sh:or` generation. The v2
schema now uses `any_of` on all 6 slots, and `gen-shacl` produces correct
`sh:or ( [ sh:datatype xsd:decimal ] [ sh:class schema:QuantitativeValue ] )`
constraints — matching v1 SHACL behaviour. The `QuantitativeValue` class with
required `minValue`/`maxValue` is also fully defined as a SHACL NodeShape.

### C3. No `sh:sparql` conditional constraints

v1 SHACL has 14 SPARQL rules enforcing: *"if boolean flag is false, the
corresponding value must not be present"*. Affected flag↔value pairs:

`WeatherWind↔weatherWindValue`, `WeatherRain↔weatherRainValue`,
`WeatherSnow↔weatherSnowValue`, `IlluminationCloudiness↔illuminationCloudinessValue`,
`DaySunElevation↔daySunElevationValue`, `TrafficAgentDensity↔trafficAgentDensityValue`,
`TrafficFlowRate↔trafficFlowRateValue`, `TrafficVolume↔trafficVolumeValue`,
`LaneSpecificationDimensions↔laneSpecificationDimensionsValue`,
`LaneSpecificationLaneCount↔laneSpecificationLaneCountValue`,
`HorizontalCurves↔horizontalCurvesValue`,
`LongitudinalDownSlope↔longitudinalDownSlopeValue`,
`LongitudinalUpSlope↔longitudinalUpSlopeValue`,
`MotionAccelerate↔motionAccelerateValue`,
`MotionDecelerate↔motionDecelerateValue`, `MotionDrive↔motionDriveValue`.

LinkML's `gen-shacl` does not support SPARQL constraint generation.

**Impact:** Business logic for conditional value presence is lost. Data with a
value but no flag will pass v2 validation but fail v1.

**Mitigation:** Document. A supplementary hand-maintained SHACL constraints file
could be added in a future iteration if needed.

### C4. `sh:closed true` vs open shapes

v2 generates `sh:closed true` (strict — rejects unknown properties). v1 shapes
are open (allow additional properties).

**Impact:** v2 is stricter. Instance data with extra properties will fail v2 but
pass v1.

**Mitigation:** Investigate `gen-shacl` flags to control closed-shape behavior.

### C5. No `rdfs:seeAlso` links

v1 classes include `rdfs:seeAlso` links to the BSI PAS-1883 specification. These
are informational metadata, not used by validation.

**Impact:** Informational loss only.

### C6. No `@en` language tags

v1 uses `rdfs:label "Text"@en` and `rdfs:comment "..."@en` with English language
tags. LinkML generates labels without language tags.

**Impact:** Minor i18n difference. Does not affect validation.

### C7. JSON-LD `@version: 1.1`

v1 context includes `"@version": 1.1`. The LinkML `gen-jsonld-context` does not
emit this.

**Impact:** May affect JSON-LD 1.1 processors expecting explicit versioning.

**Mitigation:** Investigate `gen-jsonld-context` CLI flags.

### C8. JSON-LD `rdfs:Literal` vs `xsd:string`

v1 context types admin properties as `rdfs:Literal`. v2 uses `xsd:string`.

**Impact:** `xsd:string` is more specific and precise. This is an improvement.

### C9. JSON-LD enum context blocks

v2 adds `@context` blocks with `text`, `description`, `meaning` for each enum
value. This is a standard LinkML pattern not present in v1.

**Impact:** Extra metadata in context. No harm; may be useful for tooling.

### C10. No `sh:name` / `sh:message` on property constraints

v1 includes `sh:name` and `sh:message` on every `sh:property` entry, providing
human-readable labels and error messages. LinkML's `gen-shacl` does not emit
these attributes.

**Impact:** Validation error messages are less descriptive. Default pyshacl
messages are used instead of custom messages like
`"Validation of motionDriveValue failed!"`.

### C11. No shapes graph ontology declaration

v1 declares the shapes graph as `owl:Ontology` with `owl:imports` referencing
the domain ontology. v2 does not emit a shapes graph header.

**Impact:** Tools that look for a named shapes graph via `owl:Ontology` will
not find one. Does not affect pyshacl validation.

### C12. Shape references: `sh:class` vs `sh:node`

v1 uses `sh:node openlabel:AdminTagShape` to reference sub-shapes from TagShape.
v2 uses `sh:class openlabel_v2:AdminTag` with `sh:nodeKind sh:BlankNodeOrIRI`.

**Impact:** Functionally equivalent for validation. `sh:class` checks `rdf:type`,
`sh:node` checks shape conformance. Both work for our use case.
