# Purpose and Design Philosophy

## Why These Ontologies Exist

The ENVITED-X ontologies solve a fundamental problem: **simulation assets are opaque files**. An OpenDRIVE map file, an OpenSCENARIO scenario, or an OSI trace contains rich structured data — but you cannot search across thousands of them without first understanding what's inside each one.

These ontologies provide a **searchable metadata layer** that sits alongside simulation assets, enabling discovery without parsing each file's native format.

## The Two Personas

### Data Searcher

> "Show me all HD maps of German motorways with at least 3 lanes and right-hand traffic"

The searcher doesn't want to download and parse hundreds of `.xodr` files. They need a search interface that understands simulation-domain concepts (road types, lane types, geographic coverage, accuracy) and can query structured metadata.

**How it works:**

1. A natural language query is translated into structured search slots
2. Slots are validated against the SHACL schema (ensuring valid property names and enum values)
3. A SPARQL query is compiled from the validated slots
4. The graph store returns matching assets

The [ontology-based-nl-search](https://github.com/ASCS-eV/ontology-based-nl-search) application implements this flow. The ontology IS the search schema — every property becomes a searchable facet, every enum value becomes a filter option.

### Data Creator

> "I have an OpenDRIVE 1.8 file of the A9 near Munich — how do I make it findable?"

The creator annotates their asset with JSON-LD metadata conforming to the ontology. The annotation captures what's important for discovery without duplicating the entire file content.

**How it works:**

1. The creator (or automated tooling like [sl-5-8-asset-tools](https://github.com/openMSL/sl-5-8-asset-tools)) produces a JSON-LD instance
2. The instance declares `@type: hdmap:HdMap` and populates properties (format, content, quality, quantity)
3. SHACL validation ensures the metadata is complete and values are correct
4. The validated metadata is indexed in a knowledge graph for search

### The Feedback Loop

Both personas generate feedback that improves the ontology:

- **Searcher can't find what they want** → missing property or enum value
- **Creator can't describe their asset** → missing concept or inadequate granularity
- **Search returns wrong results** → property semantics unclear or overlapping

This gap-discovery process drives ontology evolution.

## Metadata, Not Data Modeling

A critical design principle: **these ontologies describe metadata ABOUT simulation assets, not the assets themselves**.

```
┌────────────────────────────────────────────────────┐
│  SIMULATION ASSET (e.g., highway.xodr, 100MB)      │
│                                                    │
│  Contains: every road, lane, junction, signal,     │
│  geometry point, elevation sample...               │
│  Format: OpenDRIVE XSD schema (implicit ontology)  │
└────────────────────────────────────────────────────┘
                     │
                     │ DESCRIBED BY (summarized, not duplicated)
                     ▼
┌────────────────────────────────────────────────────┐
│  METADATA ANNOTATION (~2KB JSON-LD)                │
│                                                    │
│  "This file is an ASAM OpenDRIVE v1.8 map.        │
│   It covers 45km of motorway with 12 junctions.   │
│   Right-hand traffic. Lane types: driving,         │
│   shoulder. Accuracy: ±0.1m 2D."                   │
│                                                    │
│  Format: ENVITED-X ontology (explicit, searchable) │
└────────────────────────────────────────────────────┘
```

The ontology does NOT re-model OpenDRIVE's road geometry, signal semantics, or lane structure. Instead it captures the **discovery-relevant summary** of what's inside.

## Relationship to Source Standards

The ontologies relate to ASAM/ISO standards in five ways:

| Relationship | Description | Example |
|-------------|-------------|---------|
| **Aligns** | Uses the same terminology and enum values | `hdmap:roadTypes` uses OpenDRIVE `e_roadType` values verbatim |
| **Summarizes** | Counts or lists what's in the file | `numberJunctions: 12` (not each junction's structure) |
| **Extends** | Adds metadata not present in the format itself | `accuracyLaneModel2d: 0.1` (quality info external to the file) |
| **Complements** | Adds governance/provenance context | `hasManifest`, `hasResourceDescription` (Gaia-X layer) |
| **Interconnects** | Links across simulation domains | `scenario` references `hdmap` + `environment-model` |

## Design Principles

1. **Search-first** — Every property should answer a plausible user query. If no one would search by it, it's low priority.

2. **Standard-aligned** — Use the same terms as ASAM/ISO standards. Don't invent new names for existing concepts. Cite the normative source.

3. **Version-aware** — Track format versions and enforce version-appropriate constraints. OpenDRIVE 1.4 has different valid values than 1.8.

4. **Cross-domain** — Enable queries that span multiple asset types. "Find scenarios that use a specific HD map" requires linked metadata.

5. **Fail-fast validation** — SHACL shapes ensure metadata is correct at creation time, not when someone tries to search and gets bad results.

6. **Gap-discoverable** — When the search app can't answer a question, that's a signal to add a property. Document gaps explicitly.

## The Property Test

When considering adding a new ontology property, apply this test:

> **"What natural language search query does this property enable?"**

- ✅ `junctionTypes` → "Find maps with roundabouts" — clear search value
- ✅ `geometryTypes` → "Find maps with spiral road segments" — useful for tooling
- ❌ `numberOfGeometryPoints` → Nobody searches by vertex count — too low-level
- ❌ `xmlSchemaVersion` → Internal technical detail, not a discovery criterion

## Architecture Overview

```
ENVITED-X Ontology Stack
═══════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────┐
    │          Gaia-X Trust Framework              │  Governance
    │  (gx:ServiceOffering, Compliance, Trust)     │  & Identity
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │         envited-x (base layer)              │  Shared Types
    │  SimulationAsset, Manifest, ResourceDesc    │  & Wrappers
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────┬───────────┼───────────┬──────────┐
    │          │           │           │          │
    ▼          ▼           ▼           ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ hdmap  │ │scenario│ │osi-    │ │environ-│ │surface-│  Domain
│        │ │        │ │trace   │ │ment-   │ │model   │  Specific
│OpenDRIVE│ │OpenSCE-│ │OSI     │ │model   │ │OpenCRG │
│Lanelet │ │NARIO   │ │        │ │OpenMAT │ │        │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘

    ┌──────────────────────────────────────────────┐
    │       openlabel-v2 (cross-cutting)           │  ODD/Labeling
    │  ISO 34503 taxonomy, weather, road users     │  (shared by
    │  OpenODD modules, OpenLABEL types            │   multiple)
    └──────────────────────────────────────────────┘
```

Each domain ontology:

- Is a subclass of `envited-x:SimulationAsset`
- Has a `DomainSpecification` with format, content, quality, quantity facets
- Uses SHACL to validate enum values appropriate to the format version
- Can reference other domains (e.g., scenario → hdmap)

## Source Standards Reference

The [asam-openx-standards](https://github.com/ASCS-eV/asam-openx-standards) submodule (at `submodules/asam-openx-standards/`) contains version-pinned markdown copies of all referenced ASAM standards. See its `AGENTS.md` for navigation guidance and `ENUMERATIONS.yaml` for machine-readable enum data.
