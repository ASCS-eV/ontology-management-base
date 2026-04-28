## openlabel-v2 Properties

### Class Diagram

```mermaid
classDiagram
class AdminTag
class ArtificialStreetLighting
class ArtificialVehicleLighting
class Behaviour
class BehaviourCommunication
class CommunicationHeadlightFlash
class CommunicationHorn
class CommunicationSignalEmergency
class CommunicationSignalHazard
class CommunicationSignalLeft
class CommunicationSignalRight
class CommunicationSignalSlowing
class CommunicationV2i
class CommunicationV2v
class CommunicationWave
class ConnectivityCommunication
class ConnectivityPositioning
class DaySunPosition
class DrivableAreaEdge
class DrivableAreaSurfaceCondition
class DrivableAreaSurfaceFeature
class DrivableAreaSurfaceType
class DrivableAreaType
class EdgeLineMarkers
class EdgeNone
class EdgeShoulderGrass
class EdgeShoulderPavedOrGravel
class EdgeSolidBarriers
class EdgeTemporaryLineMarkers
class EnvironmentParticulates
class FixedStructureBuilding
class FixedStructureStreetFurniture
class FixedStructureStreetlight
class FixedStructureVegetation
class GeometryTransverse
class HumanAnimalRider
class HumanCyclist
class HumanDriver
class HumanMotorcyclist
class HumanPassenger
class HumanPedestrian
class HumanWheelchairUser
class IlluminationArtificial
class IlluminationLowLight
class InformationSignsUniformFullTime
class InformationSignsUniformTemporary
class InformationSignsVariableFullTime
class InformationSignsVariableTemporary
class IntersectionCrossroad
class IntersectionGradeSeperated
class IntersectionStaggered
class IntersectionTJunction
class IntersectionYJunction
class JunctionIntersection
class JunctionRoundabout
class LaneSpecificationTravelDirection
class LaneSpecificationType
class LaneTypeBus
class LaneTypeCycle
class LaneTypeEmergency
class LaneTypeSpecial
class LaneTypeTraffic
class LaneTypeTram
class LowLightAmbient
class LowLightNight
class MotorwayManaged
class MotorwayUnmanaged
class Odd
class ParticulatesDust
class ParticulatesMarine
class ParticulatesPollution
class ParticulatesVolcanic
class ParticulatesWater
class PositioningGalileo
class PositioningGlonass
class PositioningGps
class QuantitativeValue
class RainType
class RainTypeConvective
class RainTypeDynamic
class RainTypeOrographic
class RegulatorySignsUniformFullTime
class RegulatorySignsUniformTemporary
class RegulatorySignsVariableFullTime
class RegulatorySignsVariableTemporary
class RoadTypeDistributor
class RoadTypeMinor
class RoadTypeMotorway
class RoadTypeParking
class RoadTypeRadial
class RoadTypeShared
class RoadTypeSlip
class RoadUser
class RoadUserHuman
class RoadUserVehicle
class RoundaboutCompactNosignal
class RoundaboutCompactSignal
class RoundaboutDoubleNosignal
class RoundaboutDoubleSignal
class RoundaboutLargeNosignal
class RoundaboutLargeSignal
class RoundaboutMiniNosignal
class RoundaboutMiniSignal
class RoundaboutNormalNosignal
class RoundaboutNormalSignal
class Scenario
class SceneryFixedStructure
class ScenerySpecialStructure
class SceneryTemporaryStructure
class SceneryZone
class SignsInformation
class SignsRegulatory
class SignsWarning
class SpecialStructureAutoAccess
class SpecialStructureBridge
class SpecialStructurePedestrianCrossing
class SpecialStructureRailCrossing
class SpecialStructureTollPlaza
class SpecialStructureTunnel
class SunPositionBehind
class SunPositionFront
class SunPositionLeft
class SunPositionRight
class SurfaceConditionContamination
class SurfaceConditionFlooded
class SurfaceConditionIcy
class SurfaceConditionMirage
class SurfaceConditionSnow
class SurfaceConditionStandingWater
class SurfaceConditionWet
class SurfaceFeatureCrack
class SurfaceFeaturePothole
class SurfaceFeatureRut
class SurfaceFeatureSwell
class SurfaceTypeLoose
class SurfaceTypeSegmented
class SurfaceTypeUniform
class Tag
class TemporaryStructureConstructionDetour
class TemporaryStructureRefuseCollection
class TemporaryStructureRoadSignage
class TemporaryStructureRoadWorks
class TransverseBarriers
class TransverseDivided
class TransverseLanesTogether
class TransversePavements
class TransverseUndivided
class TravelDirectionLeft
class TravelDirectionRight
class V2iCellular
class V2iSatellite
class V2iWifi
class V2vCellular
class V2vSatellite
class V2vWifi
class VehicleAgricultural
class VehicleBus
class VehicleCar
class VehicleConstruction
class VehicleCycle
class VehicleEmergency
class VehicleMotorcycle
class VehicleTrailer
class VehicleTruck
class VehicleVan
class VehicleWheelchair
class WarningSignsUniform
class WarningSignsUniformFullTime
class WarningSignsUniformTemporary
class WarningSignsVariableFullTime
class WarningSignsVariableTemporary
class ZoneGeoFenced
class ZoneInterference
class ZoneRegion
class ZoneSchool
class ZoneTrafficManagement
IlluminationArtificial <|-- ArtificialStreetLighting
IlluminationArtificial <|-- ArtificialVehicleLighting
BehaviourCommunication <|-- CommunicationHeadlightFlash
BehaviourCommunication <|-- CommunicationHorn
BehaviourCommunication <|-- CommunicationSignalEmergency
BehaviourCommunication <|-- CommunicationSignalHazard
BehaviourCommunication <|-- CommunicationSignalLeft
BehaviourCommunication <|-- CommunicationSignalRight
BehaviourCommunication <|-- CommunicationSignalSlowing
ConnectivityCommunication <|-- CommunicationV2i
ConnectivityCommunication <|-- CommunicationV2v
BehaviourCommunication <|-- CommunicationWave
DrivableAreaEdge <|-- EdgeLineMarkers
DrivableAreaEdge <|-- EdgeNone
DrivableAreaEdge <|-- EdgeShoulderGrass
DrivableAreaEdge <|-- EdgeShoulderPavedOrGravel
DrivableAreaEdge <|-- EdgeSolidBarriers
DrivableAreaEdge <|-- EdgeTemporaryLineMarkers
SceneryFixedStructure <|-- FixedStructureBuilding
SceneryFixedStructure <|-- FixedStructureStreetFurniture
SceneryFixedStructure <|-- FixedStructureStreetlight
SceneryFixedStructure <|-- FixedStructureVegetation
RoadUserHuman <|-- HumanAnimalRider
RoadUserHuman <|-- HumanCyclist
RoadUserHuman <|-- HumanDriver
RoadUserHuman <|-- HumanMotorcyclist
RoadUserHuman <|-- HumanPassenger
RoadUserHuman <|-- HumanPedestrian
RoadUserHuman <|-- HumanWheelchairUser
SignsInformation <|-- InformationSignsUniformFullTime
SignsInformation <|-- InformationSignsUniformTemporary
SignsInformation <|-- InformationSignsVariableFullTime
SignsInformation <|-- InformationSignsVariableTemporary
JunctionIntersection <|-- IntersectionCrossroad
JunctionIntersection <|-- IntersectionGradeSeperated
JunctionIntersection <|-- IntersectionStaggered
JunctionIntersection <|-- IntersectionTJunction
JunctionIntersection <|-- IntersectionYJunction
LaneSpecificationType <|-- LaneTypeBus
LaneSpecificationType <|-- LaneTypeCycle
LaneSpecificationType <|-- LaneTypeEmergency
LaneSpecificationType <|-- LaneTypeSpecial
LaneSpecificationType <|-- LaneTypeTraffic
LaneSpecificationType <|-- LaneTypeTram
IlluminationLowLight <|-- LowLightAmbient
IlluminationLowLight <|-- LowLightNight
DrivableAreaType <|-- MotorwayManaged
DrivableAreaType <|-- MotorwayUnmanaged
EnvironmentParticulates <|-- ParticulatesDust
EnvironmentParticulates <|-- ParticulatesMarine
EnvironmentParticulates <|-- ParticulatesPollution
EnvironmentParticulates <|-- ParticulatesVolcanic
EnvironmentParticulates <|-- ParticulatesWater
ConnectivityPositioning <|-- PositioningGalileo
ConnectivityPositioning <|-- PositioningGlonass
ConnectivityPositioning <|-- PositioningGps
RainType <|-- RainTypeConvective
RainType <|-- RainTypeDynamic
RainType <|-- RainTypeOrographic
SignsRegulatory <|-- RegulatorySignsUniformFullTime
SignsRegulatory <|-- RegulatorySignsUniformTemporary
SignsRegulatory <|-- RegulatorySignsVariableFullTime
SignsRegulatory <|-- RegulatorySignsVariableTemporary
DrivableAreaType <|-- RoadTypeDistributor
DrivableAreaType <|-- RoadTypeMinor
DrivableAreaType <|-- RoadTypeMotorway
DrivableAreaType <|-- RoadTypeParking
DrivableAreaType <|-- RoadTypeRadial
DrivableAreaType <|-- RoadTypeShared
DrivableAreaType <|-- RoadTypeSlip
JunctionRoundabout <|-- RoundaboutCompactNosignal
JunctionRoundabout <|-- RoundaboutCompactSignal
JunctionRoundabout <|-- RoundaboutDoubleNosignal
JunctionRoundabout <|-- RoundaboutDoubleSignal
JunctionRoundabout <|-- RoundaboutLargeNosignal
JunctionRoundabout <|-- RoundaboutLargeSignal
JunctionRoundabout <|-- RoundaboutMiniNosignal
JunctionRoundabout <|-- RoundaboutMiniSignal
JunctionRoundabout <|-- RoundaboutNormalNosignal
JunctionRoundabout <|-- RoundaboutNormalSignal
ScenerySpecialStructure <|-- SpecialStructureAutoAccess
ScenerySpecialStructure <|-- SpecialStructureBridge
ScenerySpecialStructure <|-- SpecialStructurePedestrianCrossing
ScenerySpecialStructure <|-- SpecialStructureRailCrossing
ScenerySpecialStructure <|-- SpecialStructureTollPlaza
ScenerySpecialStructure <|-- SpecialStructureTunnel
DaySunPosition <|-- SunPositionBehind
DaySunPosition <|-- SunPositionFront
DaySunPosition <|-- SunPositionLeft
DaySunPosition <|-- SunPositionRight
DrivableAreaSurfaceCondition <|-- SurfaceConditionContamination
DrivableAreaSurfaceCondition <|-- SurfaceConditionFlooded
DrivableAreaSurfaceCondition <|-- SurfaceConditionIcy
DrivableAreaSurfaceCondition <|-- SurfaceConditionMirage
DrivableAreaSurfaceCondition <|-- SurfaceConditionSnow
DrivableAreaSurfaceCondition <|-- SurfaceConditionStandingWater
DrivableAreaSurfaceCondition <|-- SurfaceConditionWet
DrivableAreaSurfaceFeature <|-- SurfaceFeatureCrack
DrivableAreaSurfaceFeature <|-- SurfaceFeaturePothole
DrivableAreaSurfaceFeature <|-- SurfaceFeatureRut
DrivableAreaSurfaceFeature <|-- SurfaceFeatureSwell
DrivableAreaSurfaceType <|-- SurfaceTypeLoose
DrivableAreaSurfaceType <|-- SurfaceTypeSegmented
DrivableAreaSurfaceType <|-- SurfaceTypeUniform
SceneryTemporaryStructure <|-- TemporaryStructureConstructionDetour
SceneryTemporaryStructure <|-- TemporaryStructureRefuseCollection
SceneryTemporaryStructure <|-- TemporaryStructureRoadSignage
SceneryTemporaryStructure <|-- TemporaryStructureRoadWorks
GeometryTransverse <|-- TransverseBarriers
GeometryTransverse <|-- TransverseDivided
GeometryTransverse <|-- TransverseLanesTogether
GeometryTransverse <|-- TransversePavements
GeometryTransverse <|-- TransverseUndivided
LaneSpecificationTravelDirection <|-- TravelDirectionLeft
LaneSpecificationTravelDirection <|-- TravelDirectionRight
ConnectivityCommunication <|-- V2iCellular
ConnectivityCommunication <|-- V2iSatellite
ConnectivityCommunication <|-- V2iWifi
ConnectivityCommunication <|-- V2vCellular
ConnectivityCommunication <|-- V2vSatellite
ConnectivityCommunication <|-- V2vWifi
RoadUserVehicle <|-- VehicleAgricultural
RoadUserVehicle <|-- VehicleBus
RoadUserVehicle <|-- VehicleCar
RoadUserVehicle <|-- VehicleConstruction
RoadUserVehicle <|-- VehicleCycle
RoadUserVehicle <|-- VehicleEmergency
RoadUserVehicle <|-- VehicleMotorcycle
RoadUserVehicle <|-- VehicleTrailer
RoadUserVehicle <|-- VehicleTruck
RoadUserVehicle <|-- VehicleVan
RoadUserVehicle <|-- VehicleWheelchair
SignsWarning <|-- WarningSignsUniform
SignsWarning <|-- WarningSignsUniformFullTime
SignsWarning <|-- WarningSignsUniformTemporary
SignsWarning <|-- WarningSignsVariableFullTime
SignsWarning <|-- WarningSignsVariableTemporary
SceneryZone <|-- ZoneGeoFenced
SceneryZone <|-- ZoneInterference
SceneryZone <|-- ZoneRegion
SceneryZone <|-- ZoneSchool
SceneryZone <|-- ZoneTrafficManagement
```

### Class Hierarchy

- AdminTag (https://w3id.org/ascs-ev/envited-x/openlabel/v2/AdminTag)
- Behaviour (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Behaviour)
- BehaviourCommunication (https://w3id.org/ascs-ev/envited-x/openlabel/v2/BehaviourCommunication)
  - CommunicationHeadlightFlash (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHeadlightFlash)
  - CommunicationHorn (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHorn)
  - CommunicationSignalEmergency (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalEmergency)
  - CommunicationSignalHazard (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalHazard)
  - CommunicationSignalLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalLeft)
  - CommunicationSignalRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalRight)
  - CommunicationSignalSlowing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalSlowing)
  - CommunicationWave (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationWave)
- ConnectivityCommunication (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityCommunication)
  - CommunicationV2i (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2i)
  - CommunicationV2v (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2v)
  - V2iCellular (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iCellular)
  - V2iSatellite (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iSatellite)
  - V2iWifi (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iWifi)
  - V2vCellular (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vCellular)
  - V2vSatellite (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vSatellite)
  - V2vWifi (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vWifi)
- ConnectivityPositioning (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityPositioning)
  - PositioningGalileo (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGalileo)
  - PositioningGlonass (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGlonass)
  - PositioningGps (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGps)
- DaySunPosition (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DaySunPosition)
  - SunPositionBehind (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionBehind)
  - SunPositionFront (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionFront)
  - SunPositionLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionLeft)
  - SunPositionRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionRight)
- DrivableAreaEdge (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaEdge)
  - EdgeLineMarkers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeLineMarkers)
  - EdgeNone (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeNone)
  - EdgeShoulderGrass (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderGrass)
  - EdgeShoulderPavedOrGravel (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderPavedOrGravel)
  - EdgeSolidBarriers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeSolidBarriers)
  - EdgeTemporaryLineMarkers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeTemporaryLineMarkers)
- DrivableAreaSurfaceCondition (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceCondition)
  - SurfaceConditionContamination (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionContamination)
  - SurfaceConditionFlooded (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionFlooded)
  - SurfaceConditionIcy (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionIcy)
  - SurfaceConditionMirage (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionMirage)
  - SurfaceConditionSnow (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionSnow)
  - SurfaceConditionStandingWater (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionStandingWater)
  - SurfaceConditionWet (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionWet)
- DrivableAreaSurfaceFeature (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceFeature)
  - SurfaceFeatureCrack (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureCrack)
  - SurfaceFeaturePothole (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeaturePothole)
  - SurfaceFeatureRut (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureRut)
  - SurfaceFeatureSwell (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureSwell)
- DrivableAreaSurfaceType (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceType)
  - SurfaceTypeLoose (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeLoose)
  - SurfaceTypeSegmented (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeSegmented)
  - SurfaceTypeUniform (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeUniform)
- DrivableAreaType (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaType)
  - MotorwayManaged (https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayManaged)
  - MotorwayUnmanaged (https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayUnmanaged)
  - RoadTypeDistributor (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeDistributor)
  - RoadTypeMinor (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMinor)
  - RoadTypeMotorway (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMotorway)
  - RoadTypeParking (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeParking)
  - RoadTypeRadial (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeRadial)
  - RoadTypeShared (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeShared)
  - RoadTypeSlip (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeSlip)
- EnvironmentParticulates (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EnvironmentParticulates)
  - ParticulatesDust (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesDust)
  - ParticulatesMarine (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesMarine)
  - ParticulatesPollution (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesPollution)
  - ParticulatesVolcanic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesVolcanic)
  - ParticulatesWater (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesWater)
- GeometryTransverse (https://w3id.org/ascs-ev/envited-x/openlabel/v2/GeometryTransverse)
  - TransverseBarriers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseBarriers)
  - TransverseDivided (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseDivided)
  - TransverseLanesTogether (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseLanesTogether)
  - TransversePavements (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransversePavements)
  - TransverseUndivided (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseUndivided)
- IlluminationArtificial (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationArtificial)
  - ArtificialStreetLighting (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialStreetLighting)
  - ArtificialVehicleLighting (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialVehicleLighting)
- IlluminationLowLight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationLowLight)
  - LowLightAmbient (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightAmbient)
  - LowLightNight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightNight)
- JunctionIntersection (https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionIntersection)
  - IntersectionCrossroad (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionCrossroad)
  - IntersectionGradeSeperated (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionGradeSeperated)
  - IntersectionStaggered (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionStaggered)
  - IntersectionTJunction (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionTJunction)
  - IntersectionYJunction (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionYJunction)
- JunctionRoundabout (https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionRoundabout)
  - RoundaboutCompactNosignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactNosignal)
  - RoundaboutCompactSignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactSignal)
  - RoundaboutDoubleNosignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleNosignal)
  - RoundaboutDoubleSignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleSignal)
  - RoundaboutLargeNosignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeNosignal)
  - RoundaboutLargeSignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeSignal)
  - RoundaboutMiniNosignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniNosignal)
  - RoundaboutMiniSignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniSignal)
  - RoundaboutNormalNosignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalNosignal)
  - RoundaboutNormalSignal (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalSignal)
- LaneSpecificationTravelDirection (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTravelDirection)
  - TravelDirectionLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionLeft)
  - TravelDirectionRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionRight)
- LaneSpecificationType (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationType)
  - LaneTypeBus (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeBus)
  - LaneTypeCycle (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeCycle)
  - LaneTypeEmergency (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeEmergency)
  - LaneTypeSpecial (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeSpecial)
  - LaneTypeTraffic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTraffic)
  - LaneTypeTram (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTram)
- Odd (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Odd)
- QuantitativeValue (https://w3id.org/ascs-ev/envited-x/openlabel/v2/QuantitativeValue)
- RainType (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainType)
  - RainTypeConvective (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeConvective)
  - RainTypeDynamic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeDynamic)
  - RainTypeOrographic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeOrographic)
- RoadUser (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUser)
- RoadUserHuman (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserHuman)
  - HumanAnimalRider (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanAnimalRider)
  - HumanCyclist (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanCyclist)
  - HumanDriver (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanDriver)
  - HumanMotorcyclist (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanMotorcyclist)
  - HumanPassenger (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPassenger)
  - HumanPedestrian (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPedestrian)
  - HumanWheelchairUser (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanWheelchairUser)
- RoadUserVehicle (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserVehicle)
  - VehicleAgricultural (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleAgricultural)
  - VehicleBus (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleBus)
  - VehicleCar (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCar)
  - VehicleConstruction (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleConstruction)
  - VehicleCycle (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCycle)
  - VehicleEmergency (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleEmergency)
  - VehicleMotorcycle (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleMotorcycle)
  - VehicleTrailer (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTrailer)
  - VehicleTruck (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTruck)
  - VehicleVan (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleVan)
  - VehicleWheelchair (https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleWheelchair)
- Scenario (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Scenario)
- SceneryFixedStructure (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryFixedStructure)
  - FixedStructureBuilding (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureBuilding)
  - FixedStructureStreetFurniture (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetFurniture)
  - FixedStructureStreetlight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetlight)
  - FixedStructureVegetation (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureVegetation)
- ScenerySpecialStructure (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ScenerySpecialStructure)
  - SpecialStructureAutoAccess (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureAutoAccess)
  - SpecialStructureBridge (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureBridge)
  - SpecialStructurePedestrianCrossing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructurePedestrianCrossing)
  - SpecialStructureRailCrossing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureRailCrossing)
  - SpecialStructureTollPlaza (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTollPlaza)
  - SpecialStructureTunnel (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTunnel)
- SceneryTemporaryStructure (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryTemporaryStructure)
  - TemporaryStructureConstructionDetour (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureConstructionDetour)
  - TemporaryStructureRefuseCollection (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRefuseCollection)
  - TemporaryStructureRoadSignage (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadSignage)
  - TemporaryStructureRoadWorks (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadWorks)
- SceneryZone (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryZone)
  - ZoneGeoFenced (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneGeoFenced)
  - ZoneInterference (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneInterference)
  - ZoneRegion (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneRegion)
  - ZoneSchool (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneSchool)
  - ZoneTrafficManagement (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneTrafficManagement)
- SignsInformation (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsInformation)
  - InformationSignsUniformFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformFullTime)
  - InformationSignsUniformTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformTemporary)
  - InformationSignsVariableFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableFullTime)
  - InformationSignsVariableTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableTemporary)
- SignsRegulatory (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsRegulatory)
  - RegulatorySignsUniformFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformFullTime)
  - RegulatorySignsUniformTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformTemporary)
  - RegulatorySignsVariableFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableFullTime)
  - RegulatorySignsVariableTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableTemporary)
- SignsWarning (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsWarning)
  - WarningSignsUniform (https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniform)
  - WarningSignsUniformFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformFullTime)
  - WarningSignsUniformTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformTemporary)
  - WarningSignsVariableFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableFullTime)
  - WarningSignsVariableTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableTemporary)
- Tag (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Tag)

### Class Definitions

|Class|IRI|Description|Parents|
|---|---|---|---|
|AdminTag|https://w3id.org/ascs-ev/envited-x/openlabel/v2/AdminTag|||
|ArtificialStreetLighting|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialStreetLighting||IlluminationArtificial|
|ArtificialVehicleLighting|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialVehicleLighting||IlluminationArtificial|
|Behaviour|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Behaviour|||
|BehaviourCommunication|https://w3id.org/ascs-ev/envited-x/openlabel/v2/BehaviourCommunication|||
|CommunicationHeadlightFlash|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHeadlightFlash||BehaviourCommunication|
|CommunicationHorn|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHorn||BehaviourCommunication|
|CommunicationSignalEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalEmergency||BehaviourCommunication|
|CommunicationSignalHazard|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalHazard||BehaviourCommunication|
|CommunicationSignalLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalLeft||BehaviourCommunication|
|CommunicationSignalRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalRight||BehaviourCommunication|
|CommunicationSignalSlowing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalSlowing||BehaviourCommunication|
|CommunicationV2i|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2i||ConnectivityCommunication|
|CommunicationV2v|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2v||ConnectivityCommunication|
|CommunicationWave|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationWave||BehaviourCommunication|
|ConnectivityCommunication|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityCommunication|||
|ConnectivityPositioning|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityPositioning|||
|DaySunPosition|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DaySunPosition|||
|DrivableAreaEdge|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaEdge|||
|DrivableAreaSurfaceCondition|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceCondition|||
|DrivableAreaSurfaceFeature|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceFeature|||
|DrivableAreaSurfaceType|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceType|||
|DrivableAreaType|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaType|||
|EdgeLineMarkers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeLineMarkers||DrivableAreaEdge|
|EdgeNone|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeNone||DrivableAreaEdge|
|EdgeShoulderGrass|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderGrass||DrivableAreaEdge|
|EdgeShoulderPavedOrGravel|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderPavedOrGravel||DrivableAreaEdge|
|EdgeSolidBarriers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeSolidBarriers||DrivableAreaEdge|
|EdgeTemporaryLineMarkers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeTemporaryLineMarkers||DrivableAreaEdge|
|EnvironmentParticulates|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EnvironmentParticulates|||
|FixedStructureBuilding|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureBuilding||SceneryFixedStructure|
|FixedStructureStreetFurniture|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetFurniture||SceneryFixedStructure|
|FixedStructureStreetlight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetlight||SceneryFixedStructure|
|FixedStructureVegetation|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureVegetation||SceneryFixedStructure|
|GeometryTransverse|https://w3id.org/ascs-ev/envited-x/openlabel/v2/GeometryTransverse|||
|HumanAnimalRider|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanAnimalRider||RoadUserHuman|
|HumanCyclist|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanCyclist||RoadUserHuman|
|HumanDriver|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanDriver||RoadUserHuman|
|HumanMotorcyclist|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanMotorcyclist||RoadUserHuman|
|HumanPassenger|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPassenger||RoadUserHuman|
|HumanPedestrian|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPedestrian||RoadUserHuman|
|HumanWheelchairUser|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanWheelchairUser||RoadUserHuman|
|IlluminationArtificial|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationArtificial|||
|IlluminationLowLight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationLowLight|||
|InformationSignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformFullTime||SignsInformation|
|InformationSignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformTemporary||SignsInformation|
|InformationSignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableFullTime||SignsInformation|
|InformationSignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableTemporary||SignsInformation|
|IntersectionCrossroad|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionCrossroad||JunctionIntersection|
|IntersectionGradeSeperated|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionGradeSeperated||JunctionIntersection|
|IntersectionStaggered|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionStaggered||JunctionIntersection|
|IntersectionTJunction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionTJunction||JunctionIntersection|
|IntersectionYJunction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionYJunction||JunctionIntersection|
|JunctionIntersection|https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionIntersection|||
|JunctionRoundabout|https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionRoundabout|||
|LaneSpecificationTravelDirection|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTravelDirection|||
|LaneSpecificationType|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationType|||
|LaneTypeBus|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeBus||LaneSpecificationType|
|LaneTypeCycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeCycle||LaneSpecificationType|
|LaneTypeEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeEmergency||LaneSpecificationType|
|LaneTypeSpecial|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeSpecial||LaneSpecificationType|
|LaneTypeTraffic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTraffic||LaneSpecificationType|
|LaneTypeTram|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTram||LaneSpecificationType|
|LowLightAmbient|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightAmbient||IlluminationLowLight|
|LowLightNight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightNight||IlluminationLowLight|
|MotorwayManaged|https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayManaged||DrivableAreaType|
|MotorwayUnmanaged|https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayUnmanaged||DrivableAreaType|
|Odd|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Odd|||
|ParticulatesDust|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesDust||EnvironmentParticulates|
|ParticulatesMarine|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesMarine||EnvironmentParticulates|
|ParticulatesPollution|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesPollution||EnvironmentParticulates|
|ParticulatesVolcanic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesVolcanic||EnvironmentParticulates|
|ParticulatesWater|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesWater||EnvironmentParticulates|
|PositioningGalileo|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGalileo||ConnectivityPositioning|
|PositioningGlonass|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGlonass||ConnectivityPositioning|
|PositioningGps|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGps||ConnectivityPositioning|
|QuantitativeValue|https://w3id.org/ascs-ev/envited-x/openlabel/v2/QuantitativeValue|||
|RainType|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainType|||
|RainTypeConvective|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeConvective||RainType|
|RainTypeDynamic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeDynamic||RainType|
|RainTypeOrographic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeOrographic||RainType|
|RegulatorySignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformFullTime||SignsRegulatory|
|RegulatorySignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformTemporary||SignsRegulatory|
|RegulatorySignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableFullTime||SignsRegulatory|
|RegulatorySignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableTemporary||SignsRegulatory|
|RoadTypeDistributor|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeDistributor||DrivableAreaType|
|RoadTypeMinor|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMinor||DrivableAreaType|
|RoadTypeMotorway|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMotorway||DrivableAreaType|
|RoadTypeParking|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeParking||DrivableAreaType|
|RoadTypeRadial|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeRadial||DrivableAreaType|
|RoadTypeShared|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeShared||DrivableAreaType|
|RoadTypeSlip|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeSlip||DrivableAreaType|
|RoadUser|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUser|||
|RoadUserHuman|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserHuman|||
|RoadUserVehicle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserVehicle|||
|RoundaboutCompactNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactNosignal||JunctionRoundabout|
|RoundaboutCompactSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactSignal||JunctionRoundabout|
|RoundaboutDoubleNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleNosignal||JunctionRoundabout|
|RoundaboutDoubleSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleSignal||JunctionRoundabout|
|RoundaboutLargeNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeNosignal||JunctionRoundabout|
|RoundaboutLargeSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeSignal||JunctionRoundabout|
|RoundaboutMiniNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniNosignal||JunctionRoundabout|
|RoundaboutMiniSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniSignal||JunctionRoundabout|
|RoundaboutNormalNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalNosignal||JunctionRoundabout|
|RoundaboutNormalSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalSignal||JunctionRoundabout|
|Scenario|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Scenario|||
|SceneryFixedStructure|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryFixedStructure|||
|ScenerySpecialStructure|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ScenerySpecialStructure|||
|SceneryTemporaryStructure|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryTemporaryStructure|||
|SceneryZone|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryZone|||
|SignsInformation|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsInformation|||
|SignsRegulatory|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsRegulatory|||
|SignsWarning|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsWarning|||
|SpecialStructureAutoAccess|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureAutoAccess||ScenerySpecialStructure|
|SpecialStructureBridge|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureBridge||ScenerySpecialStructure|
|SpecialStructurePedestrianCrossing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructurePedestrianCrossing||ScenerySpecialStructure|
|SpecialStructureRailCrossing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureRailCrossing||ScenerySpecialStructure|
|SpecialStructureTollPlaza|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTollPlaza||ScenerySpecialStructure|
|SpecialStructureTunnel|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTunnel||ScenerySpecialStructure|
|SunPositionBehind|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionBehind||DaySunPosition|
|SunPositionFront|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionFront||DaySunPosition|
|SunPositionLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionLeft||DaySunPosition|
|SunPositionRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionRight||DaySunPosition|
|SurfaceConditionContamination|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionContamination||DrivableAreaSurfaceCondition|
|SurfaceConditionFlooded|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionFlooded||DrivableAreaSurfaceCondition|
|SurfaceConditionIcy|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionIcy||DrivableAreaSurfaceCondition|
|SurfaceConditionMirage|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionMirage||DrivableAreaSurfaceCondition|
|SurfaceConditionSnow|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionSnow||DrivableAreaSurfaceCondition|
|SurfaceConditionStandingWater|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionStandingWater||DrivableAreaSurfaceCondition|
|SurfaceConditionWet|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionWet||DrivableAreaSurfaceCondition|
|SurfaceFeatureCrack|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureCrack||DrivableAreaSurfaceFeature|
|SurfaceFeaturePothole|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeaturePothole||DrivableAreaSurfaceFeature|
|SurfaceFeatureRut|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureRut||DrivableAreaSurfaceFeature|
|SurfaceFeatureSwell|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureSwell||DrivableAreaSurfaceFeature|
|SurfaceTypeLoose|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeLoose||DrivableAreaSurfaceType|
|SurfaceTypeSegmented|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeSegmented||DrivableAreaSurfaceType|
|SurfaceTypeUniform|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeUniform||DrivableAreaSurfaceType|
|Tag|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Tag|||
|TemporaryStructureConstructionDetour|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureConstructionDetour||SceneryTemporaryStructure|
|TemporaryStructureRefuseCollection|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRefuseCollection||SceneryTemporaryStructure|
|TemporaryStructureRoadSignage|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadSignage||SceneryTemporaryStructure|
|TemporaryStructureRoadWorks|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadWorks||SceneryTemporaryStructure|
|TransverseBarriers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseBarriers||GeometryTransverse|
|TransverseDivided|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseDivided||GeometryTransverse|
|TransverseLanesTogether|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseLanesTogether||GeometryTransverse|
|TransversePavements|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransversePavements||GeometryTransverse|
|TransverseUndivided|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseUndivided||GeometryTransverse|
|TravelDirectionLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionLeft||LaneSpecificationTravelDirection|
|TravelDirectionRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionRight||LaneSpecificationTravelDirection|
|V2iCellular|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iCellular||ConnectivityCommunication|
|V2iSatellite|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iSatellite||ConnectivityCommunication|
|V2iWifi|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iWifi||ConnectivityCommunication|
|V2vCellular|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vCellular||ConnectivityCommunication|
|V2vSatellite|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vSatellite||ConnectivityCommunication|
|V2vWifi|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vWifi||ConnectivityCommunication|
|VehicleAgricultural|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleAgricultural||RoadUserVehicle|
|VehicleBus|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleBus||RoadUserVehicle|
|VehicleCar|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCar||RoadUserVehicle|
|VehicleConstruction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleConstruction||RoadUserVehicle|
|VehicleCycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCycle||RoadUserVehicle|
|VehicleEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleEmergency||RoadUserVehicle|
|VehicleMotorcycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleMotorcycle||RoadUserVehicle|
|VehicleTrailer|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTrailer||RoadUserVehicle|
|VehicleTruck|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTruck||RoadUserVehicle|
|VehicleVan|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleVan||RoadUserVehicle|
|VehicleWheelchair|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleWheelchair||RoadUserVehicle|
|WarningSignsUniform|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniform||SignsWarning|
|WarningSignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformFullTime||SignsWarning|
|WarningSignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformTemporary||SignsWarning|
|WarningSignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableFullTime||SignsWarning|
|WarningSignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableTemporary||SignsWarning|
|ZoneGeoFenced|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneGeoFenced||SceneryZone|
|ZoneInterference|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneInterference||SceneryZone|
|ZoneRegion|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneRegion||SceneryZone|
|ZoneSchool|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneSchool||SceneryZone|
|ZoneTrafficManagement|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneTrafficManagement||SceneryZone|

## Prefixes

- cmns-q: <https://www.omg.org/spec/Commons/Quantities/>
- openlabel_v2: <https://w3id.org/ascs-ev/envited-x/openlabel/v2/>
- rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
- rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- schema: <https://schema.org/>
- sh: <http://www.w3.org/ns/shacl#>
- xsd: <http://www.w3.org/2001/XMLSchema#>

### SHACL Properties

#### cmns-q:hasLowerBound {: #prop-https---www-omg-org-spec-commons-quantities-haslowerbound .property-anchor }
#### cmns-q:hasUpperBound {: #prop-https---www-omg-org-spec-commons-quantities-hasupperbound .property-anchor }
#### openlabel_v2:AdminTag {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-admintag .property-anchor }
#### openlabel_v2:Behaviour {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-behaviour .property-anchor }
#### openlabel_v2:BehaviourCommunication {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-behaviourcommunication .property-anchor }
#### openlabel_v2:ConnectivityCommunication {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitycommunication .property-anchor }
#### openlabel_v2:ConnectivityPositioning {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitypositioning .property-anchor }
#### openlabel_v2:DaySunElevation {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevation .property-anchor }
#### openlabel_v2:daySunElevationValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevationvalue .property-anchor }
#### openlabel_v2:DaySunPosition {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunposition .property-anchor }
#### openlabel_v2:DrivableAreaEdge {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareaedge .property-anchor }
#### openlabel_v2:DrivableAreaSurfaceCondition {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacecondition .property-anchor }
#### openlabel_v2:DrivableAreaSurfaceFeature {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacefeature .property-anchor }
#### openlabel_v2:DrivableAreaSurfaceType {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacetype .property-anchor }
#### openlabel_v2:DrivableAreaType {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareatype .property-anchor }
#### openlabel_v2:EnvironmentParticulates {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-environmentparticulates .property-anchor }
#### openlabel_v2:GeometryTransverse {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-geometrytransverse .property-anchor }
#### openlabel_v2:hasTag {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-hastag .property-anchor }
#### openlabel_v2:HorizontalCurves {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurves .property-anchor }
#### openlabel_v2:horizontalCurvesValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurvesvalue .property-anchor }
#### openlabel_v2:HorizontalStraights {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalstraights .property-anchor }
#### openlabel_v2:IlluminationArtificial {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationartificial .property-anchor }
#### openlabel_v2:IlluminationCloudiness {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudiness .property-anchor }
#### openlabel_v2:illuminationCloudinessValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudinessvalue .property-anchor }
#### openlabel_v2:IlluminationLowLight {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationlowlight .property-anchor }
#### openlabel_v2:JunctionIntersection {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionintersection .property-anchor }
#### openlabel_v2:JunctionRoundabout {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionroundabout .property-anchor }
#### openlabel_v2:LaneSpecificationDimensions {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensions .property-anchor }
#### openlabel_v2:laneSpecificationDimensionsValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensionsvalue .property-anchor }
#### openlabel_v2:LaneSpecificationLaneCount {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecount .property-anchor }
#### openlabel_v2:laneSpecificationLaneCountValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecountvalue .property-anchor }
#### openlabel_v2:LaneSpecificationMarking {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationmarking .property-anchor }
#### openlabel_v2:LaneSpecificationTravelDirection {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtraveldirection .property-anchor }
#### openlabel_v2:LaneSpecificationType {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtype .property-anchor }
#### openlabel_v2:licenseURI {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-licenseuri .property-anchor }
#### openlabel_v2:LongitudinalDownSlope {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslope .property-anchor }
#### openlabel_v2:longitudinalDownSlopeValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslopevalue .property-anchor }
#### openlabel_v2:LongitudinalLevelPlane {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinallevelplane .property-anchor }
#### openlabel_v2:LongitudinalUpSlope {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslope .property-anchor }
#### openlabel_v2:longitudinalUpSlopeValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslopevalue .property-anchor }
#### openlabel_v2:MotionAccelerate {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaccelerate .property-anchor }
#### openlabel_v2:motionAccelerateValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionacceleratevalue .property-anchor }
#### openlabel_v2:MotionAway {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaway .property-anchor }
#### openlabel_v2:MotionCross {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncross .property-anchor }
#### openlabel_v2:MotionCutIn {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutin .property-anchor }
#### openlabel_v2:MotionCutOut {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutout .property-anchor }
#### openlabel_v2:MotionDecelerate {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondecelerate .property-anchor }
#### openlabel_v2:motionDecelerateValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondeceleratevalue .property-anchor }
#### openlabel_v2:MotionDrive {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrive .property-anchor }
#### openlabel_v2:motionDriveValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrivevalue .property-anchor }
#### openlabel_v2:MotionLaneChangeLeft {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeleft .property-anchor }
#### openlabel_v2:MotionLaneChangeRight {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeright .property-anchor }
#### openlabel_v2:MotionOvertake {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionovertake .property-anchor }
#### openlabel_v2:MotionReverse {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionreverse .property-anchor }
#### openlabel_v2:MotionRun {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionrun .property-anchor }
#### openlabel_v2:MotionSlide {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionslide .property-anchor }
#### openlabel_v2:MotionStop {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionstop .property-anchor }
#### openlabel_v2:MotionTowards {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiontowards .property-anchor }
#### openlabel_v2:MotionTurn {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturn .property-anchor }
#### openlabel_v2:MotionTurnLeft {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnleft .property-anchor }
#### openlabel_v2:MotionTurnRight {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnright .property-anchor }
#### openlabel_v2:MotionUTurn {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionuturn .property-anchor }
#### openlabel_v2:MotionWalk {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionwalk .property-anchor }
#### openlabel_v2:Odd {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-odd .property-anchor }
#### openlabel_v2:ownerEmail {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-owneremail .property-anchor }
#### openlabel_v2:ownerName {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-ownername .property-anchor }
#### openlabel_v2:ownerURL {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-ownerurl .property-anchor }
#### openlabel_v2:ParticulatesDust {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesdust .property-anchor }
#### openlabel_v2:ParticulatesMarine {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesmarine .property-anchor }
#### openlabel_v2:ParticulatesPollution {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatespollution .property-anchor }
#### openlabel_v2:ParticulatesVolcanic {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesvolcanic .property-anchor }
#### openlabel_v2:particulatesWaterValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulateswatervalue .property-anchor }
#### openlabel_v2:RainType {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-raintype .property-anchor }
#### openlabel_v2:RoadUser {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduser .property-anchor }
#### openlabel_v2:RoadUserAnimal {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduseranimal .property-anchor }
#### openlabel_v2:RoadUserHuman {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduserhuman .property-anchor }
#### openlabel_v2:RoadUserVehicle {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduservehicle .property-anchor }
#### openlabel_v2:scenarioCreatedDate {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariocreateddate .property-anchor }
#### openlabel_v2:scenarioDefinition {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodefinition .property-anchor }
#### openlabel_v2:scenarioDefinitionLanguageURI {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodefinitionlanguageuri .property-anchor }
#### openlabel_v2:scenarioDescription {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodescription .property-anchor }
#### openlabel_v2:scenarioName {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioname .property-anchor }
#### openlabel_v2:scenarioParentReference {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioparentreference .property-anchor }
#### openlabel_v2:scenarioUniqueReference {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariouniquereference .property-anchor }
#### openlabel_v2:scenarioVersion {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioversion .property-anchor }
#### openlabel_v2:scenarioVisualisationURL {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariovisualisationurl .property-anchor }
#### openlabel_v2:SceneryFixedStructure {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryfixedstructure .property-anchor }
#### openlabel_v2:ScenerySpecialStructure {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryspecialstructure .property-anchor }
#### openlabel_v2:SceneryTemporaryStructure {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenerytemporarystructure .property-anchor }
#### openlabel_v2:SceneryZone {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryzone .property-anchor }
#### openlabel_v2:SignsInformation {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsinformation .property-anchor }
#### openlabel_v2:SignsRegulatory {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsregulatory .property-anchor }
#### openlabel_v2:SignsWarning {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signswarning .property-anchor }
#### openlabel_v2:SubjectVehicleSpeed {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeed .property-anchor }
#### openlabel_v2:subjectVehicleSpeedValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeedvalue .property-anchor }
#### openlabel_v2:TrafficAgentDensity {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensity .property-anchor }
#### openlabel_v2:trafficAgentDensityValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensityvalue .property-anchor }
#### openlabel_v2:TrafficAgentType {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttype .property-anchor }
#### openlabel_v2:trafficAgentTypeValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttypevalue .property-anchor }
#### openlabel_v2:TrafficFlowRate {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowrate .property-anchor }
#### openlabel_v2:trafficFlowRateValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowratevalue .property-anchor }
#### openlabel_v2:TrafficSpecialVehicle {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficspecialvehicle .property-anchor }
#### openlabel_v2:TrafficVolume {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolume .property-anchor }
#### openlabel_v2:trafficVolumeValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolumevalue .property-anchor }
#### openlabel_v2:WeatherRain {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrain .property-anchor }
#### openlabel_v2:weatherRainValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrainvalue .property-anchor }
#### openlabel_v2:WeatherSnow {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnow .property-anchor }
#### openlabel_v2:weatherSnowValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnowvalue .property-anchor }
#### openlabel_v2:WeatherWind {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwind .property-anchor }
#### openlabel_v2:weatherWindValue {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwindvalue .property-anchor }
#### schema:maxValue {: #prop-https---schema-org-maxvalue .property-anchor }
#### schema:minValue {: #prop-https---schema-org-minvalue .property-anchor }

|Shape|Property prefix|Property|MinCount|MaxCount|Description|Datatype/NodeKind|Filename|
|---|---|---|---|---|---|---|---|
|Scenario|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-hastag"></a>hasTag||1|A tag associated with a scenario.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|openlabel-v2.shacl.ttl|
|Tag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduser"></a>RoadUser||1|Road user tag.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|openlabel-v2.shacl.ttl|
|Tag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-admintag"></a>AdminTag||1|Administration tag.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|openlabel-v2.shacl.ttl|
|Tag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-behaviour"></a>Behaviour||1|Behaviour tag.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|openlabel-v2.shacl.ttl|
|Tag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-odd"></a>Odd||1|Operational Design Domain tag.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariocreateddate"></a>scenarioCreatedDate||1|The date that the scenario was created/published.|<http://www.w3.org/2001/XMLSchema#dateTime>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodefinitionlanguageuri"></a>scenarioDefinitionLanguageURI||1|URI of SDL language used for the definition of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodefinition"></a>scenarioDefinition||1|SDL definition of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioparentreference"></a>scenarioParentReference||1|Universally unique identifier (UUID) which identifies the scenario which this one has been derived from.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariodescription"></a>scenarioDescription||1|A description of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-owneremail"></a>ownerEmail||1|The email address of the legal entity who owns the rights to the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariouniquereference"></a>scenarioUniqueReference||1|Universally unique identifier (UUID) assigned to the scenario which allows the scenario to be identified.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-licenseuri"></a>licenseURI||1|The type of license which governs usage of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenariovisualisationurl"></a>scenarioVisualisationURL||1|Relative or absolute URL of a static image or animation of the scenario to allow users to easily see what the scenario represents.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-ownername"></a>ownerName||1|The name of the legal entity who owns the rights to the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioversion"></a>scenarioVersion||1|The version number of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-ownerurl"></a>ownerURL||1|The URL of the legal entity who owns the rights to the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|AdminTag|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenarioname"></a>scenarioName||1|The name of the scenario.|<http://www.w3.org/2001/XMLSchema#string>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturn"></a>MotionTurn||1|An activity where the road user changes their heading.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondeceleratevalue"></a>motionDecelerateValue||1|Rate of deceleration (ms-2).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionreverse"></a>MotionReverse||1|An activity where the subject vehicle is moving in the opposite direction to which it is facing.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutin"></a>MotionCutIn||1|An activity where the subject vehicle ends up directly in front of the object vehicle.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionstop"></a>MotionStop||1|An activity where the road user is stationary.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondecelerate"></a>MotionDecelerate||1|An activity where the road user decreases their velocity.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeright"></a>MotionLaneChangeRight||1|An activity where the subject vehicle is in a lane right of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionrun"></a>MotionRun||1|Locomotion mode where at a specific point no foot touches the ground.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionacceleratevalue"></a>motionAccelerateValue||1|Rate of acceleration (ms-2).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiontowards"></a>MotionTowards||1|An activity where the road user is closer to the object by the end.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnright"></a>MotionTurnRight||1|Subject exits the intersection on a road to the right of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaccelerate"></a>MotionAccelerate||1|An activity where the road user increases their velocity.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-behaviourcommunication"></a>BehaviourCommunication|||Communication type of road user behaviour.||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeleft"></a>MotionLaneChangeLeft||1|An activity where the subject vehicle is in a lane left of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionuturn"></a>MotionUTurn||1|Subject performs a turn resulting in heading in the opposite direction.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaway"></a>MotionAway||1|An activity where the road user is further away from the object by the end.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionovertake"></a>MotionOvertake||1|An activity where the subject starts behind and ends up in front by changing lanes.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrive"></a>MotionDrive||1|An activity where the subject vehicle is moving in the direction it is facing.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnleft"></a>MotionTurnLeft||1|Subject exits the intersection on a road to the left of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionwalk"></a>MotionWalk||1|Locomotion mode where at least one foot is always on the ground.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionslide"></a>MotionSlide||1|An activity where a pedestrian is slipping/sliding on the road.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrivevalue"></a>motionDriveValue||1|Speed (km/h).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutout"></a>MotionCutOut||1|An activity where the object vehicle suddenly moves out of the lane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncross"></a>MotionCross||1|An activity where the trajectory of the road user crosses the trajectory of the object.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslope"></a>LongitudinalUpSlope||1|Up-slope flag. Refer to BSI PAS-1883 Section 5.2.3.3.i.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwindvalue"></a>weatherWindValue||1|Wind speed (m/s). Refer to BSI PAS-1883 Section 5.3.1.1.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-geometrytransverse"></a>GeometryTransverse||1|Transverse geometry type. Refer to BSI PAS-1883 Section 5.2.3.3.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationartificial"></a>IlluminationArtificial||1|Artificial illumination type. Refer to BSI PAS-1883 Section 5.3.3.d.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsregulatory"></a>SignsRegulatory||1|Regulatory sign type. Refer to BSI PAS-1883 Section 5.2.3.5.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacetype"></a>DrivableAreaSurfaceType||1|Road surface type. Refer to BSI PAS-1883 Section 5.2.3.7.a.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryfixedstructure"></a>SceneryFixedStructure||1|Fixed road structure. Refer to BSI PAS-1883 Section 5.2.1.e.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionroundabout"></a>JunctionRoundabout||1|Roundabout type. Refer to BSI PAS-1883 Section 5.2.4.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudinessvalue"></a>illuminationCloudinessValue||1|Cloud cover (okta). Refer to BSI PAS-1883 Section 5.3.3.c.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensions"></a>LaneSpecificationDimensions||1|Lane dimensions flag. Refer to BSI PAS-1883 Section 5.2.3.4.a.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareatype"></a>DrivableAreaType||1|Road type. Refer to BSI PAS-1883 Section 5.2.3.2.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeed"></a>SubjectVehicleSpeed||1|Subject vehicle speed flag. Refer to BSI PAS-1883 Section 5.4.b.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signswarning"></a>SignsWarning||1|Warning sign type. Refer to BSI PAS-1883 Section 5.2.3.5.c.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowrate"></a>TrafficFlowRate||1|Traffic flow rate flag. Refer to BSI PAS-1883 Section 5.4.a.3.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-raintype"></a>RainType||1|Rainfall type. Refer to BSI PAS-1883 Section 5.3.1.2.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolume"></a>TrafficVolume||1|Traffic volume flag. Refer to BSI PAS-1883 Section 5.4.a.2.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensity"></a>TrafficAgentDensity||1|Traffic agent density flag. Refer to BSI PAS-1883 Section 5.4.a.1.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolumevalue"></a>trafficVolumeValue||1|Volume (vehicle km). Refer to BSI PAS-1883 Section 5.4.a.2.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionintersection"></a>JunctionIntersection||1|Intersection type. Refer to BSI PAS-1883 Section 5.2.4.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtype"></a>LaneSpecificationType|||Lane type. Refer to BSI PAS-1883 Section 5.2.3.4.c.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitycommunication"></a>ConnectivityCommunication||1|Communication connectivity type. Refer to BSI PAS-1883 Section 5.3.4.a.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevation"></a>DaySunElevation||1|Elevation of the sun above the horizon flag. Refer to BSI PAS-1883 Section 5.3.3.a.1.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowratevalue"></a>trafficFlowRateValue||1|Rate (vehicles/h). Refer to BSI PAS-1883 Section 5.4.a.3.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationmarking"></a>LaneSpecificationMarking||1|Lane marking flag. Refer to BSI PAS-1883 Section 5.2.3.4.b.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinallevelplane"></a>LongitudinalLevelPlane||1|Level plane flag. Refer to BSI PAS-1883 Section 5.2.3.3.iii.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacecondition"></a>DrivableAreaSurfaceCondition||1|Road surface condition. Refer to BSI PAS-1883 Section 5.2.3.7.c.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-environmentparticulates"></a>EnvironmentParticulates||1|Particulate type. Refer to BSI PAS-1883 Section 5.3.2.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunposition"></a>DaySunPosition||1|Position of the sun. Refer to BSI PAS-1883 Section 5.3.3.a.2.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensityvalue"></a>trafficAgentDensityValue||1|Density (vehicles/km). Refer to BSI PAS-1883 Section 5.4.a.1.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslopevalue"></a>longitudinalUpSlopeValue||1|Gradient (%). Refer to BSI PAS-1883 Section 5.2.3.3.i.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesvolcanic"></a>ParticulatesVolcanic||1|Volcanic ash flag. Refer to BSI PAS-1883 Section 5.3.2.e.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensionsvalue"></a>laneSpecificationDimensionsValue||1|Lane width (m). Refer to BSI PAS-1883 Section 5.2.3.4.a.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulateswatervalue"></a>particulatesWaterValue||1|Meteorological Optical Range (MOR) (m). Refer to BSI PAS-1883 Section 5.3.2.b.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareaedge"></a>DrivableAreaEdge|||Drivable area edge type. Refer to BSI PAS-1883 Section 5.2.3.1.e.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacefeature"></a>DrivableAreaSurfaceFeature||1|Road surface feature. Refer to BSI PAS-1883 Section 5.2.3.7.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrainvalue"></a>weatherRainValue||1|Rainfall intensity (mm/h). Refer to BSI PAS-1883 Section 5.3.1.2.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecount"></a>LaneSpecificationLaneCount||1|Number of lanes flag. Refer to BSI PAS-1883 Section 5.2.3.4.d.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurves"></a>HorizontalCurves||1|Curves flag. Refer to BSI PAS-1883 Section 5.2.3.3.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwind"></a>WeatherWind||1|Wind flag. Refer to BSI PAS-1883 Section 5.3.1.1.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficspecialvehicle"></a>TrafficSpecialVehicle||1|Presence of special vehicles flag. Refer to BSI PAS-1883 Section 5.4.a.5.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnow"></a>WeatherSnow||1|Snowfall flag. Refer to BSI PAS-1883 Section 5.3.1.3.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslopevalue"></a>longitudinalDownSlopeValue||1|Gradient (%). Refer to BSI PAS-1883 Section 5.2.3.3.ii.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationlowlight"></a>IlluminationLowLight||1|Low light condition. Refer to BSI PAS-1883 Section 5.3.3.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesdust"></a>ParticulatesDust||1|Sand and dust flag. Refer to BSI PAS-1883 Section 5.3.2.c.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslope"></a>LongitudinalDownSlope||1|Down-slope flag. Refer to BSI PAS-1883 Section 5.2.3.3.ii.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitypositioning"></a>ConnectivityPositioning||1|Positioning system type. Refer to BSI PAS-1883 Section 5.3.4.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeedvalue"></a>subjectVehicleSpeedValue||1|Speed (km/h). Refer to BSI PAS-1883 Section 5.4.b.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecountvalue"></a>laneSpecificationLaneCountValue||1|Number of lanes (unit). Refer to BSI PAS-1883 Section 5.2.3.4.d.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtraveldirection"></a>LaneSpecificationTravelDirection||1|Direction of travel. Refer to BSI PAS-1883 Section 5.2.3.4.e.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalstraights"></a>HorizontalStraights||1|Straight lines flag. Refer to BSI PAS-1883 Section 5.2.3.3.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttype"></a>TrafficAgentType||1|Traffic agent type classification flag. Refer to BSI PAS-1883 Section 5.4.a.4.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevationvalue"></a>daySunElevationValue||1|Sun elevation (degrees). Refer to BSI PAS-1883 Section 5.3.3.a.1.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttypevalue"></a>trafficAgentTypeValue|||Agent type. Refer to BSI PAS-1883 Section 5.4.a.4.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenerytemporarystructure"></a>SceneryTemporaryStructure||1|Temporary road structure. Refer to BSI PAS-1883 Section 5.2.1.f.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurvesvalue"></a>horizontalCurvesValue||1|Curve radius (m). Refer to BSI PAS-1883 Section 5.2.3.3.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrain"></a>WeatherRain||1|Rainfall flag. Refer to BSI PAS-1883 Section 5.3.1.2.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryspecialstructure"></a>ScenerySpecialStructure||1|Special road structure. Refer to BSI PAS-1883 Section 5.2.1.d.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnowvalue"></a>weatherSnowValue||1|Visibility (km). Refer to BSI PAS-1883 Section 5.3.1.3.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudiness"></a>IlluminationCloudiness||1|Cloudiness flag. Refer to BSI PAS-1883 Section 5.3.3.c.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesmarine"></a>ParticulatesMarine||1|Marine (coastal areas only) flag. Refer to BSI PAS-1883 Section 5.3.2.a.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsinformation"></a>SignsInformation||1|Information sign type. Refer to BSI PAS-1883 Section 5.2.3.5.a.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatespollution"></a>ParticulatesPollution||1|Smoke and pollution flag. Refer to BSI PAS-1883 Section 5.3.2.d.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryzone"></a>SceneryZone||1|Zone type. Refer to BSI PAS-1883 Section 5.2.1.a.||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|motionDriveValue||1|Speed (km/h).||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduservehicle"></a>RoadUserVehicle||1|Vehicle type.||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduseranimal"></a>RoadUserAnimal||1|Animal road user flag.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduserhuman"></a>RoadUserHuman||1|Human road user type.||openlabel-v2.shacl.ttl|
|QuantitativeValue|cmns-q|<a id="prop-https---www-omg-org-spec-commons-quantities-hasupperbound"></a>hasUpperBound||1|Upper bound inferred via RDFS from schema:maxValue being a subPropertyOf cmns-q:hasUpperBound in schema.org OWL.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|schema|<a id="prop-https---schema-org-minvalue"></a>minValue|1|1|Minimum value of the range.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|schema|<a id="prop-https---schema-org-maxvalue"></a>maxValue|1|1|Maximum value of the range.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|cmns-q|<a id="prop-https---www-omg-org-spec-commons-quantities-haslowerbound"></a>hasLowerBound||1|Lower bound inferred via RDFS from schema:minValue being a subPropertyOf cmns-q:hasLowerBound in schema.org OWL.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
