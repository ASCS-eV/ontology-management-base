# Using the Ontologies

The ontologies are published with stable W3ID IRIs and mirrored locally under `artifacts/`.

## W3ID Basics

W3ID provides persistent identifiers that redirect to the current location of the ontology files. Use W3ID IRIs in your data and contexts, not raw GitHub URLs.

Example patterns:

- ENVITED-X: `https://w3id.org/ascs-ev/envited-x/{domain}/{version}`
- Gaia-X4PLC-AAD: `https://w3id.org/gaia-x4plcaad/ontologies/{domain}/{version}`
- Gaia-X development: `https://w3id.org/gaia-x/development`

## Content Negotiation

W3ID IRIs use [HTTP content negotiation](https://www.w3.org/TR/cooluris/) to serve different representations of the same resource. The response depends on the `Accept` header your client sends:

| `Accept` header | Response | Description |
|---|---|---|
| `text/turtle` | `ontology.ttl` | OWL ontology definition |
| `application/ld+json` | `context.jsonld` | JSON-LD context |
| `text/html` _(browser default)_ | Documentation page | Human-readable class overview |

### Fetching artifacts with `curl`

```bash
# OWL ontology as Turtle
curl -L -H "Accept: text/turtle" https://w3id.org/ascs-ev/envited-x/manifest/v5/

# JSON-LD context
curl -L -H "Accept: application/ld+json" https://w3id.org/ascs-ev/envited-x/manifest/v5/

# SHACL shapes
curl -L -H "Accept: text/turtle" https://w3id.org/ascs-ev/envited-x/manifest/v5/shapes

# JSON-LD context via direct sub-path (no Accept header needed)
curl -L https://w3id.org/ascs-ev/envited-x/manifest/v5/context
```

### Fetching artifacts with Python

```python
import requests

response = requests.get(
    "https://w3id.org/ascs-ev/envited-x/manifest/v5/",
    headers={"Accept": "text/turtle"},
    allow_redirects=True,
)
print(response.text)  # Turtle content
```

!!! tip
    RDF tools like **rdflib**, **pyshacl**, and **Apache Jena** automatically send the correct `Accept` header when resolving ontology imports — content negotiation works transparently.

!!! note
    Opening a W3ID IRI in a browser shows the documentation page, not the raw Turtle file. This is expected behavior. Use the `curl` examples above or the `/context` sub-path to fetch machine-readable artifacts directly.

## Files You Will Use

- `*.owl.ttl` defines the ontology vocabulary
- `*.shacl.ttl` defines validation constraints
- `*.context.jsonld` provides JSON-LD prefixes and mappings

## Recommended Consumption Flow

1. Choose the ontology version from `docs/registry.json`.
2. Use the W3ID IRI in your `@context` and `@type` values.
3. Validate data with SHACL shapes before publishing.

## Local Development

For local development, the validator resolves W3ID IRIs using the XML catalogs. You do not need network access to validate data.

