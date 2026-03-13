## automotive-simulator Properties

### Class Diagram

```mermaid
classDiagram
class Class_definition_for_AutomotiveSimulator
class Class_definition_for_Content
class Class_definition_for_DomainSpecification
class Class_definition_for_Format
```

### Class Hierarchy

- Class definition for AutomotiveSimulator (https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/AutomotiveSimulator)
- Class definition for Content (https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/Content)
- Class definition for DomainSpecification (https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/DomainSpecification)
- Class definition for Format (https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/Format)

### Class Definitions

|Class|IRI|Description|Parents|
|---|---|---|---|
|Class definition for AutomotiveSimulator|https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/AutomotiveSimulator|An implementation of an automotive simulator.|SoftwareAsset|
|Class definition for Content|https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/Content|Describes the content properties of an automotive simulator (make, version, capabilities).|Content|
|Class definition for DomainSpecification|https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/DomainSpecification|Domain-specific metadata extension for automotive simulator assets.|DomainSpecification|
|Class definition for Format|https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/Format|Describes the format properties of an automotive simulator (scenario definitions, interfaces).|Format|

## Prefixes

- automotive-simulator: <https://w3id.org/gaia-x4plcaad/ontologies/automotive-simulator/v2/>
- envited-x: <https://w3id.org/ascs-ev/envited-x/envited-x/v3/>
- manifest: <https://w3id.org/ascs-ev/envited-x/manifest/v5/>
- owl: <http://www.w3.org/2002/07/owl#>
- sh: <http://www.w3.org/ns/shacl#>
- simulated-sensor: <https://w3id.org/gaia-x4plcaad/ontologies/simulated-sensor/v2/>
- skos: <http://www.w3.org/2004/02/skos/core#>
- xsd: <http://www.w3.org/2001/XMLSchema#>

### SHACL Properties

#### automotive-simulator:hasContent {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hascontent .property-anchor }
#### automotive-simulator:hasDomainSpecification {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasdomainspecification .property-anchor }
#### automotive-simulator:hasFormat {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasformat .property-anchor }
#### automotive-simulator:hasManifest {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasmanifest .property-anchor }
#### automotive-simulator:hasSoftwareResource {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hassoftwareresource .property-anchor }
#### automotive-simulator:interface {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-interface .property-anchor }
#### automotive-simulator:scenarioDefinition {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-scenariodefinition .property-anchor }
#### automotive-simulator:sensorAttackFlag {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-sensorattackflag .property-anchor }
#### automotive-simulator:sensorFailureFlag {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-sensorfailureflag .property-anchor }
#### automotive-simulator:simulatorMake {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-simulatormake .property-anchor }
#### automotive-simulator:softwareVersion {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-softwareversion .property-anchor }
#### simulated-sensor:simulatedSensor {: #prop-https---w3id-org-gaia-x4plcaad-ontologies-simulated-sensor-v2-simulatedsensor .property-anchor }

|Shape|Property prefix|Property|MinCount|MaxCount|Description|Datatype/NodeKind|Filename|
|---|---|---|---|---|---|---|---|
|AutomotiveSimulatorShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hassoftwareresource"></a>hasSoftwareResource|1|1|||automotive-simulator.shacl.ttl|
|AutomotiveSimulatorShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasdomainspecification"></a>hasDomainSpecification|1|1|||automotive-simulator.shacl.ttl|
|AutomotiveSimulatorShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasmanifest"></a>hasManifest|1|1|||automotive-simulator.shacl.ttl|
|DomainSpecificationShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hascontent"></a>hasContent|1|1|||automotive-simulator.shacl.ttl|
|DomainSpecificationShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-hasformat"></a>hasFormat|1|1|||automotive-simulator.shacl.ttl|
|ContentShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-simulatormake"></a>simulatorMake|1|1|Make/Type of automotive simulator.|<http://www.w3.org/2001/XMLSchema#string>|automotive-simulator.shacl.ttl|
|ContentShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-softwareversion"></a>softwareVersion|1|1|Software version of the simulator.|<http://www.w3.org/2001/XMLSchema#string>|automotive-simulator.shacl.ttl|
|ContentShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-sensorfailureflag"></a>sensorFailureFlag|1|1|If true, the simulator supports the simulation of sensor failures.|<http://www.w3.org/2001/XMLSchema#boolean>|automotive-simulator.shacl.ttl|
|ContentShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-sensorattackflag"></a>sensorAttackFlag|1|1|If true, the simulator supports the simulation of sensor attacks.|<http://www.w3.org/2001/XMLSchema#boolean>|automotive-simulator.shacl.ttl|
|ContentShape|simulated-sensor|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-simulated-sensor-v2-simulatedsensor"></a>simulatedSensor|0||Type and kinds of sensors that are natively included in the simulator.||automotive-simulator.shacl.ttl|
|FormatShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-scenariodefinition"></a>scenarioDefinition|0||Description language for defining driving scenarios supported by the simulator.|<http://www.w3.org/2001/XMLSchema#string>|automotive-simulator.shacl.ttl|
|FormatShape|automotive-simulator|<a id="prop-https---w3id-org-gaia-x4plcaad-ontologies-automotive-simulator-v2-interface"></a>interface|0||Communication interface provided by the simulator.|<http://www.w3.org/2001/XMLSchema#string>|automotive-simulator.shacl.ttl|
