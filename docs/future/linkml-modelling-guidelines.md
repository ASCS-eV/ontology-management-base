# LinkML Naming & Modelling Guidelines

This document defines naming conventions and modelling patterns for LinkML
schemas in this repository. These guidelines are distilled from established
ontology engineering best practices and reference implementations.

## Authoritative Sources

| Source | Key Principle | URL |
|--------|---------------|-----|
| W3C SWBP "Specified Values" | Suffix value-partition classes with `_value` | <https://www.w3.org/TR/swbp-specified-values/> |
| schema.org Style Guide | *"Do not give the same name to a type and a property"* | <https://schema.org/docs/styleguide.html> |
| schema.org Enumeration | ~70% of enumerations use `...Enumeration` or `...Type` suffix | <https://schema.org/Enumeration> |
| Biolink Model | All enums suffixed: `DrugAvailabilityEnum`, `AgentTypeEnum` | <https://github.com/biolink/biolink-model> |
| OWL Guide (W3C 2004) | Range classes use compound nouns distinct from properties | <https://www.w3.org/TR/owl-guide/> |
| OWL 2 Primer (W3C 2012) | Property names use `has-`/`-of` prefixes for disambiguation | <https://www.w3.org/TR/owl2-primer/> |
| Ontology Development 101 | Properties get `has-`/`-of`; avoid `class`/`property` in names | Stanford/Protégé |
| FHIR Terminology | Compound PascalCase nouns for CodeSystems; path-based separation | <https://www.hl7.org/fhir/terminologies.html> |
| DCAT 3 | Semantic suffixes on range classes (`ConceptScheme`, `Taxonomy`) | <https://www.w3.org/ns/dcat#> |

---

## Rule 1 — Class Names: UpperCamelCase Nouns

Classes represent **things** or **categories**. Name them as singular nouns in
UpperCamelCase.

```yaml
classes:
  Tag:
    description: A scenario annotation tag.
  QuantitativeValue:
    description: A numeric measurement with unit.
```

**Rationale:** OWL Guide §3, Ontology 101 §4; universal convention across
schema.org, FHIR, SKOS, Dublin Core.

---

## Rule 2 — Enum Names: UpperCamelCase + `Enum` Suffix

Enumerations represent **closed value sets**. Always append `Enum` to the class
name to distinguish the value-set class from any same-named property.

```yaml
enums:
  WeatherRainEnum:
    description: Types of precipitation.
    permissible_values:
      RainLight: { description: Light rain. }
      RainHeavy: { description: Heavy rain. }
```

**Do not** set `enum_uri` for collision avoidance — the suffix in the name
produces the correct IRI automatically via LinkML's `class_curie` default.

**Rationale:**

- **Biolink Model** (canonical LinkML schema): all enums use `Enum` suffix
  (`DrugAvailabilityEnum`, `AgentTypeEnum`, `KnowledgeLevelEnum`).
- **schema.org**: *"Do not give the same name to a type and a property"*;
  uses `...Enumeration`/`...Type` suffixes on ~70% of value-set classes.
- **W3C SWBP Specified Values**: explicitly recommends `_value` suffix on
  value-partition subclasses.
- **LinkML gen-owl**: emits `owl:Class` for enums and `owl:ObjectProperty`
  for slots. Without suffix, same-named slot+enum produces IRI punning.

---

## Rule 3 — Slot Names: lowerCamelCase Descriptive Names

Slots represent **properties** or **relationships**. Use lowerCamelCase.
For composition relationships where the slot name would otherwise collide
with a class name, use the class name directly (OWL 2 DL permits
class/property punning for this pattern).

```yaml
slots:
  weatherWindValue:
    description: Wind speed in metres per second.
    range: integer
  WeatherRain:
    description: Type of precipitation.
    range: WeatherRainEnum
```

**Rationale:** OWL 2 Primer §4.4 recommends descriptive property names;
Ontology 101 §6.3 suggests `has-`/`-of` prefixes. For data-bearing slots
(literals), lowerCamelCase is universal. For object slots whose range is an
enum, the slot name matches the domain concept (not the enum class).

---

## Rule 4 — Slot URIs: Use `slot_uri` Only for External Alignment

Do **not** set `slot_uri` to work around naming collisions. If a collision
exists, fix the **name**. Use `slot_uri` only to align a slot with an
externally-defined property IRI (e.g., `dcterms:title`, `schema:name`).

```yaml
slots:
  name:
    slot_uri: schema:name    # ← external alignment (correct use)
    range: string
```

---

## Rule 5 — Enum URI: Use `enum_uri` Only for External Value Sets

The `enum_uri` field is documented for linking an enum to an **existing
external value set** (e.g., a FHIR ValueSet or LOINC hierarchy). Do **not**
use it as a collision-avoidance mechanism.

```yaml
enums:
  LoincExampleEnum:
    enum_uri: http://hl7.org/fhir/ValueSet/example-intensional  # ← external (correct)
```

**Rationale:** The only official LinkML example of `enum_uri` links to a
FHIR ValueSet. Biolink, NMDC, and the LinkML metamodel itself never set
`enum_uri` for internal enums.

---

## Rule 6 — Permissible Values: UpperCamelCase Specific Names

Permissible values within enums represent **individuals** or **leaf concepts**.
Use UpperCamelCase compound nouns that are self-descriptive.

```yaml
permissible_values:
  RainLight:
    description: Light rain or drizzle.
  RainHeavy:
    description: Heavy rain or downpour.
```

**Rationale:** OWL Guide uses `White`, `Rose`, `Red` for wine colors;
schema.org uses `ReadPermission`, `WritePermission`. Compound nouns avoid
collision with unrelated concepts.

---

## Rule 7 — Avoid IRI Punning Between Slots and Enums

The same IRI must **never** denote both an `owl:ObjectProperty` and the
`owl:Class` that serves as its `rdfs:range`. This creates circular
self-reference (a property whose range is "itself").

| Pattern | Result | Status |
|---------|--------|--------|
| Slot `WeatherRain` + Enum `WeatherRain` | Same IRI = Class + Property | ❌ Punned |
| Slot `WeatherRain` + Enum `WeatherRainEnum` | Distinct IRIs | ✅ Clean |

**Detection:** After generating OWL, verify no IRI appears as both
`owl:Class` and `owl:ObjectProperty` (except intentional composition slots
where class/property punning is the accepted pattern per Rule 3).

---

## Rule 8 — Composition Slots May Share IRI with Their Range Class

When a slot represents a **structural composition** relationship (a class
containing a sub-object of a specific type), the slot name **may** match the
class name. This is an accepted OWL 2 DL pattern (class/property punning is
explicitly permitted by the W3C OWL 2 specification §2.4.1).

```yaml
classes:
  AdminTag:
    description: Administration tag.
slots:
  AdminTag:
    description: Administration tag.
    range: AdminTag
    inlined: true
```

This is acceptable because:

- OWL 2 DL explicitly allows same IRI as Class + ObjectProperty
- The JSON-LD key stays human-readable (`"AdminTag": {...}`)
- Established precedent: FHIR BackboneElements, schema.org nested types

---

## Summary Table

| Element | Naming Convention | Example |
|---------|-------------------|---------|
| Class | `UpperCamelCase` noun | `Tag`, `QuantitativeValue` |
| Enum | `UpperCamelCase` + `Enum` | `WeatherRainEnum` |
| Permissible Value | `UpperCamelCase` compound | `RainLight`, `RainHeavy` |
| Data slot | `lowerCamelCase` | `weatherWindValue` |
| Object slot (enum range) | `UpperCamelCase` (matches concept) | `WeatherRain` |
| Composition slot | `UpperCamelCase` (matches class) | `AdminTag` |

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| Enum name = Slot name (no suffix) | IRI punning: same IRI as Class + Property | Add `Enum` suffix to enum name |
| Using `enum_uri` for disambiguation | Not idiomatic; `enum_uri` is for external alignment | Rename the enum instead |
| Using `slot_uri` to avoid collision | gen-owl ignores `slot_uri` when slot name = class name | Rename the slot or accept composition punning |
| Property named same as class (casing only) | Fragile; some serializations are case-insensitive | Use compound names or suffixes |
