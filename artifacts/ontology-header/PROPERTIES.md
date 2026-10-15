## ontology-header Properties

### Class Diagram

```mermaid
classDiagram
class OntologyHeader
```

### Class Hierarchy

- OntologyHeader (https://w3id.org/ascs-ev/envited-x/ontology-header/v1/OntologyHeader)

### Class Definitions

|Class|IRI|Description|Parents|
|---|---|---|---|
|OntologyHeader|https://w3id.org/ascs-ev/envited-x/ontology-header/v1/OntologyHeader|The header of an ENVITED-X ontology. An ontology whose LinkML schema instantiates this class is typed with it, and its header is checked against these constraints.||

## Prefixes

- dcterms: <http://purl.org/dc/terms/>
- ontology-header: <https://w3id.org/ascs-ev/envited-x/ontology-header/v1/>
- owl: <http://www.w3.org/2002/07/owl#>
- prov: <http://www.w3.org/ns/prov#>
- rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
- rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- sh: <http://www.w3.org/ns/shacl#>
- xsd: <http://www.w3.org/2001/XMLSchema#>

### SHACL Properties

#### dcterms:publisher {: #prop-http---purl-org-dc-terms-publisher .property-anchor }
#### dcterms:references {: #prop-http---purl-org-dc-terms-references .property-anchor }
#### owl:priorVersion {: #prop-http---www-w3-org-2002-07-owl-priorversion .property-anchor }
#### prov:wasDerivedFrom {: #prop-http---www-w3-org-ns-prov-wasderivedfrom .property-anchor }

|Shape|Property prefix|Property|MinCount|MaxCount|Description|Datatype/NodeKind|Filename|
|---|---|---|---|---|---|---|---|
|OntologyHeaderShape|dcterms|<a id="prop-http---purl-org-dc-terms-publisher"></a>publisher|1|1|The organisation that publishes the ontology.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ontology-header.shacl.ttl|
|OntologyHeaderShape|dcterms|<a id="prop-http---purl-org-dc-terms-references"></a>references||1|A related ontology or specification the ontology builds on.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ontology-header.shacl.ttl|
|OntologyHeaderShape|prov|<a id="prop-http---www-w3-org-ns-prov-wasderivedfrom"></a>wasDerivedFrom|1|1|The release of the repository this version is published from.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ontology-header.shacl.ttl|
|OntologyHeaderShape|owl|<a id="prop-http---www-w3-org-2002-07-owl-priorversion"></a>priorVersion||1|The ontology IRI of the version this one replaces. Absent from a first version.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ontology-header.shacl.ttl|
