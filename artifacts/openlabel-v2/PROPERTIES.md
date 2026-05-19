## openlabel-v2 Properties

### Class Diagram

```mermaid
classDiagram
class AdminTag
class ArtificialStreetLighting
class ArtificialVehicleLighting
class Behaviour
class BehaviourCommunicationEnum
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
class ConnectivityCommunicationEnum
class ConnectivityPositioningEnum
class DaySunPositionEnum
class DrivableAreaEdgeEnum
class DrivableAreaSurfaceConditionEnum
class DrivableAreaSurfaceFeatureEnum
class DrivableAreaSurfaceTypeEnum
class DrivableAreaTypeEnum
class EdgeLineMarkers
class EdgeNone
class EdgeShoulderGrass
class EdgeShoulderPavedOrGravel
class EdgeSolidBarriers
class EdgeTemporaryLineMarkers
class EnvironmentParticulatesEnum
class FixedStructureBuilding
class FixedStructureStreetFurniture
class FixedStructureStreetlight
class FixedStructureVegetation
class GeometryTransverseEnum
class HumanAnimalRider
class HumanCyclist
class HumanDriver
class HumanMotorcyclist
class HumanPassenger
class HumanPedestrian
class HumanWheelchairUser
class IlluminationArtificialEnum
class IlluminationLowLightEnum
class InformationSignsUniformFullTime
class InformationSignsUniformTemporary
class InformationSignsVariableFullTime
class InformationSignsVariableTemporary
class IntersectionCrossroad
class IntersectionGradeSeperated
class IntersectionStaggered
class IntersectionTJunction
class IntersectionYJunction
class JunctionIntersectionEnum
class JunctionRoundaboutEnum
class LaneSpecificationTravelDirectionEnum
class LaneSpecificationTypeEnum
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
class OddDynamicElements
class OddEnvironment
class OddScenery
class ParticulatesDust
class ParticulatesMarine
class ParticulatesPollution
class ParticulatesVolcanic
class ParticulatesWater
class PositioningGalileo
class PositioningGlonass
class PositioningGps
class QuantitativeValue
class RainTypeConvective
class RainTypeDynamic
class RainTypeEnum
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
class RoadUserHumanEnum
class RoadUserVehicleEnum
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
class SceneryFixedStructureEnum
class ScenerySpecialStructureEnum
class SceneryTemporaryStructureEnum
class SceneryZoneEnum
class SignsInformationEnum
class SignsRegulatoryEnum
class SignsWarningEnum
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
IlluminationArtificialEnum <|-- ArtificialStreetLighting
IlluminationArtificialEnum <|-- ArtificialVehicleLighting
BehaviourCommunicationEnum <|-- CommunicationHeadlightFlash
BehaviourCommunicationEnum <|-- CommunicationHorn
BehaviourCommunicationEnum <|-- CommunicationSignalEmergency
BehaviourCommunicationEnum <|-- CommunicationSignalHazard
BehaviourCommunicationEnum <|-- CommunicationSignalLeft
BehaviourCommunicationEnum <|-- CommunicationSignalRight
BehaviourCommunicationEnum <|-- CommunicationSignalSlowing
ConnectivityCommunicationEnum <|-- CommunicationV2i
ConnectivityCommunicationEnum <|-- CommunicationV2v
BehaviourCommunicationEnum <|-- CommunicationWave
DrivableAreaEdgeEnum <|-- EdgeLineMarkers
DrivableAreaEdgeEnum <|-- EdgeNone
DrivableAreaEdgeEnum <|-- EdgeShoulderGrass
DrivableAreaEdgeEnum <|-- EdgeShoulderPavedOrGravel
DrivableAreaEdgeEnum <|-- EdgeSolidBarriers
DrivableAreaEdgeEnum <|-- EdgeTemporaryLineMarkers
SceneryFixedStructureEnum <|-- FixedStructureBuilding
SceneryFixedStructureEnum <|-- FixedStructureStreetFurniture
SceneryFixedStructureEnum <|-- FixedStructureStreetlight
SceneryFixedStructureEnum <|-- FixedStructureVegetation
RoadUserHumanEnum <|-- HumanAnimalRider
RoadUserHumanEnum <|-- HumanCyclist
RoadUserHumanEnum <|-- HumanDriver
RoadUserHumanEnum <|-- HumanMotorcyclist
RoadUserHumanEnum <|-- HumanPassenger
RoadUserHumanEnum <|-- HumanPedestrian
RoadUserHumanEnum <|-- HumanWheelchairUser
SignsInformationEnum <|-- InformationSignsUniformFullTime
SignsInformationEnum <|-- InformationSignsUniformTemporary
SignsInformationEnum <|-- InformationSignsVariableFullTime
SignsInformationEnum <|-- InformationSignsVariableTemporary
JunctionIntersectionEnum <|-- IntersectionCrossroad
JunctionIntersectionEnum <|-- IntersectionGradeSeperated
JunctionIntersectionEnum <|-- IntersectionStaggered
JunctionIntersectionEnum <|-- IntersectionTJunction
JunctionIntersectionEnum <|-- IntersectionYJunction
LaneSpecificationTypeEnum <|-- LaneTypeBus
LaneSpecificationTypeEnum <|-- LaneTypeCycle
LaneSpecificationTypeEnum <|-- LaneTypeEmergency
LaneSpecificationTypeEnum <|-- LaneTypeSpecial
LaneSpecificationTypeEnum <|-- LaneTypeTraffic
LaneSpecificationTypeEnum <|-- LaneTypeTram
IlluminationLowLightEnum <|-- LowLightAmbient
IlluminationLowLightEnum <|-- LowLightNight
DrivableAreaTypeEnum <|-- MotorwayManaged
DrivableAreaTypeEnum <|-- MotorwayUnmanaged
Odd <|-- OddDynamicElements
Odd <|-- OddEnvironment
Odd <|-- OddScenery
EnvironmentParticulatesEnum <|-- ParticulatesDust
EnvironmentParticulatesEnum <|-- ParticulatesMarine
EnvironmentParticulatesEnum <|-- ParticulatesPollution
EnvironmentParticulatesEnum <|-- ParticulatesVolcanic
EnvironmentParticulatesEnum <|-- ParticulatesWater
ConnectivityPositioningEnum <|-- PositioningGalileo
ConnectivityPositioningEnum <|-- PositioningGlonass
ConnectivityPositioningEnum <|-- PositioningGps
RainTypeEnum <|-- RainTypeConvective
RainTypeEnum <|-- RainTypeDynamic
RainTypeEnum <|-- RainTypeOrographic
SignsRegulatoryEnum <|-- RegulatorySignsUniformFullTime
SignsRegulatoryEnum <|-- RegulatorySignsUniformTemporary
SignsRegulatoryEnum <|-- RegulatorySignsVariableFullTime
SignsRegulatoryEnum <|-- RegulatorySignsVariableTemporary
DrivableAreaTypeEnum <|-- RoadTypeDistributor
DrivableAreaTypeEnum <|-- RoadTypeMinor
DrivableAreaTypeEnum <|-- RoadTypeMotorway
DrivableAreaTypeEnum <|-- RoadTypeParking
DrivableAreaTypeEnum <|-- RoadTypeRadial
DrivableAreaTypeEnum <|-- RoadTypeShared
DrivableAreaTypeEnum <|-- RoadTypeSlip
JunctionRoundaboutEnum <|-- RoundaboutCompactNosignal
JunctionRoundaboutEnum <|-- RoundaboutCompactSignal
JunctionRoundaboutEnum <|-- RoundaboutDoubleNosignal
JunctionRoundaboutEnum <|-- RoundaboutDoubleSignal
JunctionRoundaboutEnum <|-- RoundaboutLargeNosignal
JunctionRoundaboutEnum <|-- RoundaboutLargeSignal
JunctionRoundaboutEnum <|-- RoundaboutMiniNosignal
JunctionRoundaboutEnum <|-- RoundaboutMiniSignal
JunctionRoundaboutEnum <|-- RoundaboutNormalNosignal
JunctionRoundaboutEnum <|-- RoundaboutNormalSignal
ScenerySpecialStructureEnum <|-- SpecialStructureAutoAccess
ScenerySpecialStructureEnum <|-- SpecialStructureBridge
ScenerySpecialStructureEnum <|-- SpecialStructurePedestrianCrossing
ScenerySpecialStructureEnum <|-- SpecialStructureRailCrossing
ScenerySpecialStructureEnum <|-- SpecialStructureTollPlaza
ScenerySpecialStructureEnum <|-- SpecialStructureTunnel
DaySunPositionEnum <|-- SunPositionBehind
DaySunPositionEnum <|-- SunPositionFront
DaySunPositionEnum <|-- SunPositionLeft
DaySunPositionEnum <|-- SunPositionRight
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionContamination
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionFlooded
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionIcy
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionMirage
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionSnow
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionStandingWater
DrivableAreaSurfaceConditionEnum <|-- SurfaceConditionWet
DrivableAreaSurfaceFeatureEnum <|-- SurfaceFeatureCrack
DrivableAreaSurfaceFeatureEnum <|-- SurfaceFeaturePothole
DrivableAreaSurfaceFeatureEnum <|-- SurfaceFeatureRut
DrivableAreaSurfaceFeatureEnum <|-- SurfaceFeatureSwell
DrivableAreaSurfaceTypeEnum <|-- SurfaceTypeLoose
DrivableAreaSurfaceTypeEnum <|-- SurfaceTypeSegmented
DrivableAreaSurfaceTypeEnum <|-- SurfaceTypeUniform
SceneryTemporaryStructureEnum <|-- TemporaryStructureConstructionDetour
SceneryTemporaryStructureEnum <|-- TemporaryStructureRefuseCollection
SceneryTemporaryStructureEnum <|-- TemporaryStructureRoadSignage
SceneryTemporaryStructureEnum <|-- TemporaryStructureRoadWorks
GeometryTransverseEnum <|-- TransverseBarriers
GeometryTransverseEnum <|-- TransverseDivided
GeometryTransverseEnum <|-- TransverseLanesTogether
GeometryTransverseEnum <|-- TransversePavements
GeometryTransverseEnum <|-- TransverseUndivided
LaneSpecificationTravelDirectionEnum <|-- TravelDirectionLeft
LaneSpecificationTravelDirectionEnum <|-- TravelDirectionRight
ConnectivityCommunicationEnum <|-- V2iCellular
ConnectivityCommunicationEnum <|-- V2iSatellite
ConnectivityCommunicationEnum <|-- V2iWifi
ConnectivityCommunicationEnum <|-- V2vCellular
ConnectivityCommunicationEnum <|-- V2vSatellite
ConnectivityCommunicationEnum <|-- V2vWifi
RoadUserVehicleEnum <|-- VehicleAgricultural
RoadUserVehicleEnum <|-- VehicleBus
RoadUserVehicleEnum <|-- VehicleCar
RoadUserVehicleEnum <|-- VehicleConstruction
RoadUserVehicleEnum <|-- VehicleCycle
RoadUserVehicleEnum <|-- VehicleEmergency
RoadUserVehicleEnum <|-- VehicleMotorcycle
RoadUserVehicleEnum <|-- VehicleTrailer
RoadUserVehicleEnum <|-- VehicleTruck
RoadUserVehicleEnum <|-- VehicleVan
RoadUserVehicleEnum <|-- VehicleWheelchair
SignsWarningEnum <|-- WarningSignsUniform
SignsWarningEnum <|-- WarningSignsUniformFullTime
SignsWarningEnum <|-- WarningSignsUniformTemporary
SignsWarningEnum <|-- WarningSignsVariableFullTime
SignsWarningEnum <|-- WarningSignsVariableTemporary
SceneryZoneEnum <|-- ZoneGeoFenced
SceneryZoneEnum <|-- ZoneInterference
SceneryZoneEnum <|-- ZoneRegion
SceneryZoneEnum <|-- ZoneSchool
SceneryZoneEnum <|-- ZoneTrafficManagement
```

### Class Hierarchy

- AdminTag (https://w3id.org/ascs-ev/envited-x/openlabel/v2/AdminTag)
- Behaviour (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Behaviour)
- BehaviourCommunicationEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/BehaviourCommunicationEnum)
  - CommunicationHeadlightFlash (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHeadlightFlash)
  - CommunicationHorn (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHorn)
  - CommunicationSignalEmergency (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalEmergency)
  - CommunicationSignalHazard (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalHazard)
  - CommunicationSignalLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalLeft)
  - CommunicationSignalRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalRight)
  - CommunicationSignalSlowing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalSlowing)
  - CommunicationWave (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationWave)
- ConnectivityCommunicationEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityCommunicationEnum)
  - CommunicationV2i (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2i)
  - CommunicationV2v (https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2v)
  - V2iCellular (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iCellular)
  - V2iSatellite (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iSatellite)
  - V2iWifi (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iWifi)
  - V2vCellular (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vCellular)
  - V2vSatellite (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vSatellite)
  - V2vWifi (https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vWifi)
- ConnectivityPositioningEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityPositioningEnum)
  - PositioningGalileo (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGalileo)
  - PositioningGlonass (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGlonass)
  - PositioningGps (https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGps)
- DaySunPositionEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DaySunPositionEnum)
  - SunPositionBehind (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionBehind)
  - SunPositionFront (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionFront)
  - SunPositionLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionLeft)
  - SunPositionRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionRight)
- DrivableAreaEdgeEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaEdgeEnum)
  - EdgeLineMarkers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeLineMarkers)
  - EdgeNone (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeNone)
  - EdgeShoulderGrass (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderGrass)
  - EdgeShoulderPavedOrGravel (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderPavedOrGravel)
  - EdgeSolidBarriers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeSolidBarriers)
  - EdgeTemporaryLineMarkers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeTemporaryLineMarkers)
- DrivableAreaSurfaceConditionEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceConditionEnum)
  - SurfaceConditionContamination (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionContamination)
  - SurfaceConditionFlooded (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionFlooded)
  - SurfaceConditionIcy (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionIcy)
  - SurfaceConditionMirage (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionMirage)
  - SurfaceConditionSnow (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionSnow)
  - SurfaceConditionStandingWater (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionStandingWater)
  - SurfaceConditionWet (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionWet)
- DrivableAreaSurfaceFeatureEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceFeatureEnum)
  - SurfaceFeatureCrack (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureCrack)
  - SurfaceFeaturePothole (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeaturePothole)
  - SurfaceFeatureRut (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureRut)
  - SurfaceFeatureSwell (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureSwell)
- DrivableAreaSurfaceTypeEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceTypeEnum)
  - SurfaceTypeLoose (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeLoose)
  - SurfaceTypeSegmented (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeSegmented)
  - SurfaceTypeUniform (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeUniform)
- DrivableAreaTypeEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaTypeEnum)
  - MotorwayManaged (https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayManaged)
  - MotorwayUnmanaged (https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayUnmanaged)
  - RoadTypeDistributor (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeDistributor)
  - RoadTypeMinor (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMinor)
  - RoadTypeMotorway (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMotorway)
  - RoadTypeParking (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeParking)
  - RoadTypeRadial (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeRadial)
  - RoadTypeShared (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeShared)
  - RoadTypeSlip (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeSlip)
- EnvironmentParticulatesEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/EnvironmentParticulatesEnum)
  - ParticulatesDust (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesDust)
  - ParticulatesMarine (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesMarine)
  - ParticulatesPollution (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesPollution)
  - ParticulatesVolcanic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesVolcanic)
  - ParticulatesWater (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesWater)
- GeometryTransverseEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/GeometryTransverseEnum)
  - TransverseBarriers (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseBarriers)
  - TransverseDivided (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseDivided)
  - TransverseLanesTogether (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseLanesTogether)
  - TransversePavements (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransversePavements)
  - TransverseUndivided (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseUndivided)
- IlluminationArtificialEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationArtificialEnum)
  - ArtificialStreetLighting (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialStreetLighting)
  - ArtificialVehicleLighting (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialVehicleLighting)
- IlluminationLowLightEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationLowLightEnum)
  - LowLightAmbient (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightAmbient)
  - LowLightNight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightNight)
- JunctionIntersectionEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionIntersectionEnum)
  - IntersectionCrossroad (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionCrossroad)
  - IntersectionGradeSeperated (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionGradeSeperated)
  - IntersectionStaggered (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionStaggered)
  - IntersectionTJunction (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionTJunction)
  - IntersectionYJunction (https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionYJunction)
- JunctionRoundaboutEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionRoundaboutEnum)
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
- LaneSpecificationTravelDirectionEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTravelDirectionEnum)
  - TravelDirectionLeft (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionLeft)
  - TravelDirectionRight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionRight)
- LaneSpecificationTypeEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTypeEnum)
  - LaneTypeBus (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeBus)
  - LaneTypeCycle (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeCycle)
  - LaneTypeEmergency (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeEmergency)
  - LaneTypeSpecial (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeSpecial)
  - LaneTypeTraffic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTraffic)
  - LaneTypeTram (https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTram)
- Odd (https://w3id.org/ascs-ev/envited-x/openlabel/v2/Odd)
  - OddDynamicElements (https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddDynamicElements)
  - OddEnvironment (https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddEnvironment)
  - OddScenery (https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddScenery)
- QuantitativeValue (https://w3id.org/ascs-ev/envited-x/openlabel/v2/QuantitativeValue)
- RainTypeEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeEnum)
  - RainTypeConvective (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeConvective)
  - RainTypeDynamic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeDynamic)
  - RainTypeOrographic (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeOrographic)
- RoadUser (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUser)
- RoadUserHumanEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserHumanEnum)
  - HumanAnimalRider (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanAnimalRider)
  - HumanCyclist (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanCyclist)
  - HumanDriver (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanDriver)
  - HumanMotorcyclist (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanMotorcyclist)
  - HumanPassenger (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPassenger)
  - HumanPedestrian (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPedestrian)
  - HumanWheelchairUser (https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanWheelchairUser)
- RoadUserVehicleEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserVehicleEnum)
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
- SceneryFixedStructureEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryFixedStructureEnum)
  - FixedStructureBuilding (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureBuilding)
  - FixedStructureStreetFurniture (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetFurniture)
  - FixedStructureStreetlight (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetlight)
  - FixedStructureVegetation (https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureVegetation)
- ScenerySpecialStructureEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ScenerySpecialStructureEnum)
  - SpecialStructureAutoAccess (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureAutoAccess)
  - SpecialStructureBridge (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureBridge)
  - SpecialStructurePedestrianCrossing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructurePedestrianCrossing)
  - SpecialStructureRailCrossing (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureRailCrossing)
  - SpecialStructureTollPlaza (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTollPlaza)
  - SpecialStructureTunnel (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTunnel)
- SceneryTemporaryStructureEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryTemporaryStructureEnum)
  - TemporaryStructureConstructionDetour (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureConstructionDetour)
  - TemporaryStructureRefuseCollection (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRefuseCollection)
  - TemporaryStructureRoadSignage (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadSignage)
  - TemporaryStructureRoadWorks (https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadWorks)
- SceneryZoneEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryZoneEnum)
  - ZoneGeoFenced (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneGeoFenced)
  - ZoneInterference (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneInterference)
  - ZoneRegion (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneRegion)
  - ZoneSchool (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneSchool)
  - ZoneTrafficManagement (https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneTrafficManagement)
- SignsInformationEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsInformationEnum)
  - InformationSignsUniformFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformFullTime)
  - InformationSignsUniformTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformTemporary)
  - InformationSignsVariableFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableFullTime)
  - InformationSignsVariableTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableTemporary)
- SignsRegulatoryEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsRegulatoryEnum)
  - RegulatorySignsUniformFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformFullTime)
  - RegulatorySignsUniformTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformTemporary)
  - RegulatorySignsVariableFullTime (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableFullTime)
  - RegulatorySignsVariableTemporary (https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableTemporary)
- SignsWarningEnum (https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsWarningEnum)
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
|ArtificialStreetLighting|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialStreetLighting||IlluminationArtificialEnum|
|ArtificialVehicleLighting|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ArtificialVehicleLighting||IlluminationArtificialEnum|
|Behaviour|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Behaviour|||
|BehaviourCommunicationEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/BehaviourCommunicationEnum|||
|CommunicationHeadlightFlash|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHeadlightFlash||BehaviourCommunicationEnum|
|CommunicationHorn|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationHorn||BehaviourCommunicationEnum|
|CommunicationSignalEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalEmergency||BehaviourCommunicationEnum|
|CommunicationSignalHazard|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalHazard||BehaviourCommunicationEnum|
|CommunicationSignalLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalLeft||BehaviourCommunicationEnum|
|CommunicationSignalRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalRight||BehaviourCommunicationEnum|
|CommunicationSignalSlowing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationSignalSlowing||BehaviourCommunicationEnum|
|CommunicationV2i|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2i||ConnectivityCommunicationEnum|
|CommunicationV2v|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationV2v||ConnectivityCommunicationEnum|
|CommunicationWave|https://w3id.org/ascs-ev/envited-x/openlabel/v2/CommunicationWave||BehaviourCommunicationEnum|
|ConnectivityCommunicationEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityCommunicationEnum|||
|ConnectivityPositioningEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ConnectivityPositioningEnum|||
|DaySunPositionEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DaySunPositionEnum|||
|DrivableAreaEdgeEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaEdgeEnum|||
|DrivableAreaSurfaceConditionEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceConditionEnum|||
|DrivableAreaSurfaceFeatureEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceFeatureEnum|||
|DrivableAreaSurfaceTypeEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaSurfaceTypeEnum|||
|DrivableAreaTypeEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/DrivableAreaTypeEnum|||
|EdgeLineMarkers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeLineMarkers||DrivableAreaEdgeEnum|
|EdgeNone|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeNone||DrivableAreaEdgeEnum|
|EdgeShoulderGrass|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderGrass||DrivableAreaEdgeEnum|
|EdgeShoulderPavedOrGravel|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeShoulderPavedOrGravel||DrivableAreaEdgeEnum|
|EdgeSolidBarriers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeSolidBarriers||DrivableAreaEdgeEnum|
|EdgeTemporaryLineMarkers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EdgeTemporaryLineMarkers||DrivableAreaEdgeEnum|
|EnvironmentParticulatesEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/EnvironmentParticulatesEnum|||
|FixedStructureBuilding|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureBuilding||SceneryFixedStructureEnum|
|FixedStructureStreetFurniture|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetFurniture||SceneryFixedStructureEnum|
|FixedStructureStreetlight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureStreetlight||SceneryFixedStructureEnum|
|FixedStructureVegetation|https://w3id.org/ascs-ev/envited-x/openlabel/v2/FixedStructureVegetation||SceneryFixedStructureEnum|
|GeometryTransverseEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/GeometryTransverseEnum|||
|HumanAnimalRider|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanAnimalRider||RoadUserHumanEnum|
|HumanCyclist|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanCyclist||RoadUserHumanEnum|
|HumanDriver|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanDriver||RoadUserHumanEnum|
|HumanMotorcyclist|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanMotorcyclist||RoadUserHumanEnum|
|HumanPassenger|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPassenger||RoadUserHumanEnum|
|HumanPedestrian|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanPedestrian||RoadUserHumanEnum|
|HumanWheelchairUser|https://w3id.org/ascs-ev/envited-x/openlabel/v2/HumanWheelchairUser||RoadUserHumanEnum|
|IlluminationArtificialEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationArtificialEnum|||
|IlluminationLowLightEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IlluminationLowLightEnum|||
|InformationSignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformFullTime||SignsInformationEnum|
|InformationSignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsUniformTemporary||SignsInformationEnum|
|InformationSignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableFullTime||SignsInformationEnum|
|InformationSignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/InformationSignsVariableTemporary||SignsInformationEnum|
|IntersectionCrossroad|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionCrossroad||JunctionIntersectionEnum|
|IntersectionGradeSeperated|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionGradeSeperated||JunctionIntersectionEnum|
|IntersectionStaggered|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionStaggered||JunctionIntersectionEnum|
|IntersectionTJunction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionTJunction||JunctionIntersectionEnum|
|IntersectionYJunction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/IntersectionYJunction||JunctionIntersectionEnum|
|JunctionIntersectionEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionIntersectionEnum|||
|JunctionRoundaboutEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/JunctionRoundaboutEnum|||
|LaneSpecificationTravelDirectionEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTravelDirectionEnum|||
|LaneSpecificationTypeEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneSpecificationTypeEnum|||
|LaneTypeBus|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeBus||LaneSpecificationTypeEnum|
|LaneTypeCycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeCycle||LaneSpecificationTypeEnum|
|LaneTypeEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeEmergency||LaneSpecificationTypeEnum|
|LaneTypeSpecial|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeSpecial||LaneSpecificationTypeEnum|
|LaneTypeTraffic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTraffic||LaneSpecificationTypeEnum|
|LaneTypeTram|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LaneTypeTram||LaneSpecificationTypeEnum|
|LowLightAmbient|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightAmbient||IlluminationLowLightEnum|
|LowLightNight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/LowLightNight||IlluminationLowLightEnum|
|MotorwayManaged|https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayManaged||DrivableAreaTypeEnum|
|MotorwayUnmanaged|https://w3id.org/ascs-ev/envited-x/openlabel/v2/MotorwayUnmanaged||DrivableAreaTypeEnum|
|Odd|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Odd|||
|OddDynamicElements|https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddDynamicElements||Odd|
|OddEnvironment|https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddEnvironment||Odd|
|OddScenery|https://w3id.org/ascs-ev/envited-x/openlabel/v2/OddScenery||Odd|
|ParticulatesDust|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesDust||EnvironmentParticulatesEnum|
|ParticulatesMarine|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesMarine||EnvironmentParticulatesEnum|
|ParticulatesPollution|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesPollution||EnvironmentParticulatesEnum|
|ParticulatesVolcanic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesVolcanic||EnvironmentParticulatesEnum|
|ParticulatesWater|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ParticulatesWater||EnvironmentParticulatesEnum|
|PositioningGalileo|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGalileo||ConnectivityPositioningEnum|
|PositioningGlonass|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGlonass||ConnectivityPositioningEnum|
|PositioningGps|https://w3id.org/ascs-ev/envited-x/openlabel/v2/PositioningGps||ConnectivityPositioningEnum|
|QuantitativeValue|https://w3id.org/ascs-ev/envited-x/openlabel/v2/QuantitativeValue|||
|RainTypeConvective|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeConvective||RainTypeEnum|
|RainTypeDynamic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeDynamic||RainTypeEnum|
|RainTypeEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeEnum|||
|RainTypeOrographic|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RainTypeOrographic||RainTypeEnum|
|RegulatorySignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformFullTime||SignsRegulatoryEnum|
|RegulatorySignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsUniformTemporary||SignsRegulatoryEnum|
|RegulatorySignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableFullTime||SignsRegulatoryEnum|
|RegulatorySignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RegulatorySignsVariableTemporary||SignsRegulatoryEnum|
|RoadTypeDistributor|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeDistributor||DrivableAreaTypeEnum|
|RoadTypeMinor|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMinor||DrivableAreaTypeEnum|
|RoadTypeMotorway|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeMotorway||DrivableAreaTypeEnum|
|RoadTypeParking|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeParking||DrivableAreaTypeEnum|
|RoadTypeRadial|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeRadial||DrivableAreaTypeEnum|
|RoadTypeShared|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeShared||DrivableAreaTypeEnum|
|RoadTypeSlip|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadTypeSlip||DrivableAreaTypeEnum|
|RoadUser|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUser|||
|RoadUserHumanEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserHumanEnum|||
|RoadUserVehicleEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoadUserVehicleEnum|||
|RoundaboutCompactNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactNosignal||JunctionRoundaboutEnum|
|RoundaboutCompactSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutCompactSignal||JunctionRoundaboutEnum|
|RoundaboutDoubleNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleNosignal||JunctionRoundaboutEnum|
|RoundaboutDoubleSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutDoubleSignal||JunctionRoundaboutEnum|
|RoundaboutLargeNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeNosignal||JunctionRoundaboutEnum|
|RoundaboutLargeSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutLargeSignal||JunctionRoundaboutEnum|
|RoundaboutMiniNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniNosignal||JunctionRoundaboutEnum|
|RoundaboutMiniSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutMiniSignal||JunctionRoundaboutEnum|
|RoundaboutNormalNosignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalNosignal||JunctionRoundaboutEnum|
|RoundaboutNormalSignal|https://w3id.org/ascs-ev/envited-x/openlabel/v2/RoundaboutNormalSignal||JunctionRoundaboutEnum|
|Scenario|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Scenario|||
|SceneryFixedStructureEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryFixedStructureEnum|||
|ScenerySpecialStructureEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ScenerySpecialStructureEnum|||
|SceneryTemporaryStructureEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryTemporaryStructureEnum|||
|SceneryZoneEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SceneryZoneEnum|||
|SignsInformationEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsInformationEnum|||
|SignsRegulatoryEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsRegulatoryEnum|||
|SignsWarningEnum|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SignsWarningEnum|||
|SpecialStructureAutoAccess|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureAutoAccess||ScenerySpecialStructureEnum|
|SpecialStructureBridge|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureBridge||ScenerySpecialStructureEnum|
|SpecialStructurePedestrianCrossing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructurePedestrianCrossing||ScenerySpecialStructureEnum|
|SpecialStructureRailCrossing|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureRailCrossing||ScenerySpecialStructureEnum|
|SpecialStructureTollPlaza|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTollPlaza||ScenerySpecialStructureEnum|
|SpecialStructureTunnel|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SpecialStructureTunnel||ScenerySpecialStructureEnum|
|SunPositionBehind|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionBehind||DaySunPositionEnum|
|SunPositionFront|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionFront||DaySunPositionEnum|
|SunPositionLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionLeft||DaySunPositionEnum|
|SunPositionRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SunPositionRight||DaySunPositionEnum|
|SurfaceConditionContamination|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionContamination||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionFlooded|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionFlooded||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionIcy|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionIcy||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionMirage|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionMirage||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionSnow|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionSnow||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionStandingWater|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionStandingWater||DrivableAreaSurfaceConditionEnum|
|SurfaceConditionWet|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceConditionWet||DrivableAreaSurfaceConditionEnum|
|SurfaceFeatureCrack|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureCrack||DrivableAreaSurfaceFeatureEnum|
|SurfaceFeaturePothole|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeaturePothole||DrivableAreaSurfaceFeatureEnum|
|SurfaceFeatureRut|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureRut||DrivableAreaSurfaceFeatureEnum|
|SurfaceFeatureSwell|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceFeatureSwell||DrivableAreaSurfaceFeatureEnum|
|SurfaceTypeLoose|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeLoose||DrivableAreaSurfaceTypeEnum|
|SurfaceTypeSegmented|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeSegmented||DrivableAreaSurfaceTypeEnum|
|SurfaceTypeUniform|https://w3id.org/ascs-ev/envited-x/openlabel/v2/SurfaceTypeUniform||DrivableAreaSurfaceTypeEnum|
|Tag|https://w3id.org/ascs-ev/envited-x/openlabel/v2/Tag|||
|TemporaryStructureConstructionDetour|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureConstructionDetour||SceneryTemporaryStructureEnum|
|TemporaryStructureRefuseCollection|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRefuseCollection||SceneryTemporaryStructureEnum|
|TemporaryStructureRoadSignage|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadSignage||SceneryTemporaryStructureEnum|
|TemporaryStructureRoadWorks|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TemporaryStructureRoadWorks||SceneryTemporaryStructureEnum|
|TransverseBarriers|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseBarriers||GeometryTransverseEnum|
|TransverseDivided|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseDivided||GeometryTransverseEnum|
|TransverseLanesTogether|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseLanesTogether||GeometryTransverseEnum|
|TransversePavements|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransversePavements||GeometryTransverseEnum|
|TransverseUndivided|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TransverseUndivided||GeometryTransverseEnum|
|TravelDirectionLeft|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionLeft||LaneSpecificationTravelDirectionEnum|
|TravelDirectionRight|https://w3id.org/ascs-ev/envited-x/openlabel/v2/TravelDirectionRight||LaneSpecificationTravelDirectionEnum|
|V2iCellular|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iCellular||ConnectivityCommunicationEnum|
|V2iSatellite|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iSatellite||ConnectivityCommunicationEnum|
|V2iWifi|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2iWifi||ConnectivityCommunicationEnum|
|V2vCellular|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vCellular||ConnectivityCommunicationEnum|
|V2vSatellite|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vSatellite||ConnectivityCommunicationEnum|
|V2vWifi|https://w3id.org/ascs-ev/envited-x/openlabel/v2/V2vWifi||ConnectivityCommunicationEnum|
|VehicleAgricultural|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleAgricultural||RoadUserVehicleEnum|
|VehicleBus|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleBus||RoadUserVehicleEnum|
|VehicleCar|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCar||RoadUserVehicleEnum|
|VehicleConstruction|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleConstruction||RoadUserVehicleEnum|
|VehicleCycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleCycle||RoadUserVehicleEnum|
|VehicleEmergency|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleEmergency||RoadUserVehicleEnum|
|VehicleMotorcycle|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleMotorcycle||RoadUserVehicleEnum|
|VehicleTrailer|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTrailer||RoadUserVehicleEnum|
|VehicleTruck|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleTruck||RoadUserVehicleEnum|
|VehicleVan|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleVan||RoadUserVehicleEnum|
|VehicleWheelchair|https://w3id.org/ascs-ev/envited-x/openlabel/v2/VehicleWheelchair||RoadUserVehicleEnum|
|WarningSignsUniform|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniform||SignsWarningEnum|
|WarningSignsUniformFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformFullTime||SignsWarningEnum|
|WarningSignsUniformTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsUniformTemporary||SignsWarningEnum|
|WarningSignsVariableFullTime|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableFullTime||SignsWarningEnum|
|WarningSignsVariableTemporary|https://w3id.org/ascs-ev/envited-x/openlabel/v2/WarningSignsVariableTemporary||SignsWarningEnum|
|ZoneGeoFenced|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneGeoFenced||SceneryZoneEnum|
|ZoneInterference|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneInterference||SceneryZoneEnum|
|ZoneRegion|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneRegion||SceneryZoneEnum|
|ZoneSchool|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneSchool||SceneryZoneEnum|
|ZoneTrafficManagement|https://w3id.org/ascs-ev/envited-x/openlabel/v2/ZoneTrafficManagement||SceneryZoneEnum|

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
#### openlabel_v2:ParticulatesWater {: #prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulateswater .property-anchor }
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
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-scenerytemporarystructure"></a>SceneryTemporaryStructure||0|Type of temporary drivable area structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudiness"></a>IlluminationCloudiness||0|Presence of cloudiness.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-raintype"></a>RainType||0|Type of rainfall.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationlowlight"></a>IlluminationLowLight||0|Type of low-light condition.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwind"></a>WeatherWind||0|Presence of wind.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationcloudinessvalue"></a>illuminationCloudinessValue||0|Cloud cover in okta.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrain"></a>WeatherRain||0|Presence of rainfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacecondition"></a>DrivableAreaSurfaceCondition||0|Type of drivable area surface condition.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslope"></a>LongitudinalUpSlope||0|Presence of an uphill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinalupslopevalue"></a>longitudinalUpSlopeValue||0|Upward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-illuminationartificial"></a>IlluminationArtificial||0|Type of artificial illumination.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryspecialstructure"></a>ScenerySpecialStructure||0|Type of special structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecountvalue"></a>laneSpecificationLaneCountValue||0|Number of lanes.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsinformation"></a>SignsInformation||0|Type of information sign.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherwindvalue"></a>weatherWindValue||0|Wind speed in metres per second.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signsregulatory"></a>SignsRegulatory||0|Type of regulatory sign.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunposition"></a>DaySunPosition||0|Position of the sun relative to the direction of travel.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-environmentparticulates"></a>EnvironmentParticulates||0|Type of particulates present in the environment.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurves"></a>HorizontalCurves||0|Presence of curved roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weatherrainvalue"></a>weatherRainValue||0|Rainfall intensity in millimetres per hour.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesmarine"></a>ParticulatesMarine||0|Presence of marine spray in coastal areas.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulateswatervalue"></a>particulatesWaterValue||0|Meteorological optical range in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowratevalue"></a>trafficFlowRateValue||1|Traffic flow rate in vehicles per hour.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulateswater"></a>ParticulatesWater||0|Presence of non-precipitating water droplets or ice crystals.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesvolcanic"></a>ParticulatesVolcanic||0|Presence of volcanic ash particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeed"></a>SubjectVehicleSpeed||1|Presence of a specified subject vehicle speed.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacetype"></a>DrivableAreaSurfaceType||0|Type of drivable area surface.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficflowrate"></a>TrafficFlowRate||1|Presence of a specified traffic flow rate.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareasurfacefeature"></a>DrivableAreaSurfaceFeature||0|Type of drivable area surface feature.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatespollution"></a>ParticulatesPollution||0|Presence of smoke or pollution particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttype"></a>TrafficAgentType||1|Presence of a specified traffic agent type.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensity"></a>TrafficAgentDensity||1|Presence of a specified traffic agent density.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryfixedstructure"></a>SceneryFixedStructure||0|Type of basic road structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslopevalue"></a>longitudinalDownSlopeValue||0|Downward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensionsvalue"></a>laneSpecificationDimensionsValue||0|Lane width in metres.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionroundabout"></a>JunctionRoundabout||0|Type of roundabout.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationlanecount"></a>LaneSpecificationLaneCount||0|Presence of a specified lane count.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-geometrytransverse"></a>GeometryTransverse||0|Type of transverse geometry.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-sceneryzone"></a>SceneryZone||0|Type of zone.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtype"></a>LaneSpecificationType||0|Type of lane.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareaedge"></a>DrivableAreaEdge||0|Type of drivable area edge.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnow"></a>WeatherSnow||0|Presence of snowfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevation"></a>DaySunElevation||0|Presence of a specified sun elevation above the horizon.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationtraveldirection"></a>LaneSpecificationTravelDirection||0|Direction of travel.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-particulatesdust"></a>ParticulatesDust||0|Presence of sand or dust particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolume"></a>TrafficVolume||1|Presence of a specified traffic volume.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitypositioning"></a>ConnectivityPositioning||0|Type of positioning system.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficspecialvehicle"></a>TrafficSpecialVehicle||1|Presence of special vehicles.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-subjectvehiclespeedvalue"></a>subjectVehicleSpeedValue||1|Subject vehicle speed in kilometres per hour.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationmarking"></a>LaneSpecificationMarking||0|Presence of lane markings.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-daysunelevationvalue"></a>daySunElevationValue||0|Sun elevation in degrees.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagenttypevalue"></a>trafficAgentTypeValue|||Types of traffic agents present.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficagentdensityvalue"></a>trafficAgentDensityValue||1|Traffic agent density in vehicles per kilometre.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-trafficvolumevalue"></a>trafficVolumeValue||1|Traffic volume in vehicle kilometres.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-signswarning"></a>SignsWarning||0|Type of warning sign.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-connectivitycommunication"></a>ConnectivityCommunication||0|Type of communication connectivity.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinaldownslope"></a>LongitudinalDownSlope||0|Presence of a downhill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-lanespecificationdimensions"></a>LaneSpecificationDimensions||0|Presence of specified lane dimensions.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-drivableareatype"></a>DrivableAreaType||0|Type of drivable area.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-junctionintersection"></a>JunctionIntersection||0|Type of intersection.||openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalstraights"></a>HorizontalStraights||0|Presence of straight roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-horizontalcurvesvalue"></a>horizontalCurvesValue||0|Curve radius in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-longitudinallevelplane"></a>LongitudinalLevelPlane||0|Presence of a level longitudinal plane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddDynamicElements|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-weathersnowvalue"></a>weatherSnowValue||0|Visibility in kilometres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DrivableAreaSurfaceType||0|Type of drivable area surface.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ParticulatesWater||1|Presence of non-precipitating water droplets or ice crystals.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DrivableAreaSurfaceFeature||0|Type of drivable area surface feature.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|illuminationCloudinessValue||1|Cloud cover in okta.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SubjectVehicleSpeed||0|Presence of a specified subject vehicle speed.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|longitudinalDownSlopeValue||0|Downward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|GeometryTransverse||0|Type of transverse geometry.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SceneryTemporaryStructure||0|Type of temporary drivable area structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LaneSpecificationType||0|Type of lane.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|laneSpecificationLaneCountValue||0|Number of lanes.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LaneSpecificationDimensions||0|Presence of specified lane dimensions.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|IlluminationCloudiness||1|Presence of cloudiness.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|JunctionIntersection||0|Type of intersection.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|TrafficVolume||0|Presence of a specified traffic volume.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LongitudinalUpSlope||0|Presence of an uphill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|TrafficAgentType||0|Presence of a specified traffic agent type.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|trafficVolumeValue||0|Traffic volume in vehicle kilometres.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ScenerySpecialStructure||0|Type of special structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|TrafficAgentDensity||0|Presence of a specified traffic agent density.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SignsWarning||0|Type of warning sign.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LongitudinalLevelPlane||0|Presence of a level longitudinal plane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|TrafficFlowRate||0|Presence of a specified traffic flow rate.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|weatherRainValue||1|Rainfall intensity in millimetres per hour.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SceneryFixedStructure||0|Type of basic road structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|TrafficSpecialVehicle||0|Presence of special vehicles.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ConnectivityCommunication||1|Type of communication connectivity.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ParticulatesPollution||1|Presence of smoke or pollution particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|RainType||1|Type of rainfall.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|laneSpecificationDimensionsValue||0|Lane width in metres.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DaySunPosition||1|Position of the sun relative to the direction of travel.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|HorizontalCurves||0|Presence of curved roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DaySunElevation||1|Presence of a specified sun elevation above the horizon.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|EnvironmentParticulates||1|Type of particulates present in the environment.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|trafficFlowRateValue||0|Traffic flow rate in vehicles per hour.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ParticulatesMarine||1|Presence of marine spray in coastal areas.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|longitudinalUpSlopeValue||0|Upward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|IlluminationLowLight||1|Type of low-light condition.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|WeatherWind||1|Presence of wind.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ParticulatesDust||1|Presence of sand or dust particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LaneSpecificationMarking||0|Presence of lane markings.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DrivableAreaSurfaceCondition||0|Type of drivable area surface condition.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LongitudinalDownSlope||0|Presence of a downhill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LaneSpecificationLaneCount||0|Presence of a specified lane count.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|WeatherRain||1|Presence of rainfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|weatherWindValue||1|Wind speed in metres per second.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|HorizontalStraights||0|Presence of straight roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|trafficAgentDensityValue||0|Traffic agent density in vehicles per kilometre.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ConnectivityPositioning||1|Type of positioning system.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|horizontalCurvesValue||0|Curve radius in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|IlluminationArtificial||1|Type of artificial illumination.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SignsInformation||0|Type of information sign.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DrivableAreaType||0|Type of drivable area.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|trafficAgentTypeValue||0|Types of traffic agents present.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|daySunElevationValue||1|Sun elevation in degrees.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SceneryZone||0|Type of zone.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|DrivableAreaEdge||0|Type of drivable area edge.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|subjectVehicleSpeedValue||0|Subject vehicle speed in kilometres per hour.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|SignsRegulatory||0|Type of regulatory sign.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|ParticulatesVolcanic||1|Presence of volcanic ash particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|JunctionRoundabout||0|Type of roundabout.||openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|WeatherSnow||1|Presence of snowfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|weatherSnowValue||1|Visibility in kilometres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|particulatesWaterValue||1|Meteorological optical range in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddEnvironment|openlabel_v2|LaneSpecificationTravelDirection||0|Direction of travel.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|RainType||0|Type of rainfall.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ParticulatesVolcanic||0|Presence of volcanic ash particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SignsRegulatory||1|Type of regulatory sign.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|trafficAgentDensityValue||0|Traffic agent density in vehicles per kilometre.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SceneryTemporaryStructure||1|Type of temporary drivable area structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|TrafficVolume||0|Presence of a specified traffic volume.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|TrafficAgentDensity||0|Presence of a specified traffic agent density.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|WeatherSnow||0|Presence of snowfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|IlluminationArtificial||0|Type of artificial illumination.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|weatherRainValue||0|Rainfall intensity in millimetres per hour.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ConnectivityCommunication||0|Type of communication connectivity.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|trafficVolumeValue||0|Traffic volume in vehicle kilometres.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ParticulatesPollution||0|Presence of smoke or pollution particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ParticulatesDust||0|Presence of sand or dust particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LaneSpecificationType|||Type of lane.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|HorizontalCurves||1|Presence of curved roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LaneSpecificationDimensions||1|Presence of specified lane dimensions.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SceneryFixedStructure||1|Type of basic road structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DrivableAreaSurfaceType||1|Type of drivable area surface.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ConnectivityPositioning||0|Type of positioning system.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|TrafficAgentType||0|Presence of a specified traffic agent type.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DrivableAreaSurfaceFeature||1|Type of drivable area surface feature.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DaySunElevation||0|Presence of a specified sun elevation above the horizon.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|JunctionIntersection||1|Type of intersection.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|illuminationCloudinessValue||0|Cloud cover in okta.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|JunctionRoundabout||1|Type of roundabout.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|EnvironmentParticulates||0|Type of particulates present in the environment.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|TrafficSpecialVehicle||0|Presence of special vehicles.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LongitudinalLevelPlane||1|Presence of a level longitudinal plane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|weatherWindValue||0|Wind speed in metres per second.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|WeatherWind||0|Presence of wind.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DaySunPosition||0|Position of the sun relative to the direction of travel.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|GeometryTransverse||1|Type of transverse geometry.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ScenerySpecialStructure||1|Type of special structure present in the scenery.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|horizontalCurvesValue||1|Curve radius in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|WeatherRain||0|Presence of rainfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LaneSpecificationMarking||1|Presence of lane markings.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ParticulatesWater||0|Presence of non-precipitating water droplets or ice crystals.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|TrafficFlowRate||0|Presence of a specified traffic flow rate.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|HorizontalStraights||1|Presence of straight roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|laneSpecificationDimensionsValue||1|Lane width in metres.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DrivableAreaEdge|||Type of drivable area edge.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|trafficAgentTypeValue||0|Types of traffic agents present.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DrivableAreaSurfaceCondition||1|Type of drivable area surface condition.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|weatherSnowValue||0|Visibility in kilometres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|ParticulatesMarine||0|Presence of marine spray in coastal areas.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LaneSpecificationLaneCount||1|Presence of a specified lane count.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LongitudinalUpSlope||1|Presence of an uphill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|IlluminationCloudiness||0|Presence of cloudiness.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|laneSpecificationLaneCountValue||1|Number of lanes.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LaneSpecificationTravelDirection||1|Direction of travel.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|IlluminationLowLight||0|Type of low-light condition.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|LongitudinalDownSlope||1|Presence of a downhill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|DrivableAreaType||1|Type of drivable area.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|particulatesWaterValue||0|Meteorological optical range in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|daySunElevationValue||0|Sun elevation in degrees.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SceneryZone||1|Type of zone.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|longitudinalUpSlopeValue||1|Upward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SubjectVehicleSpeed||0|Presence of a specified subject vehicle speed.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|subjectVehicleSpeedValue||0|Subject vehicle speed in kilometres per hour.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SignsInformation||1|Type of information sign.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|trafficFlowRateValue||0|Traffic flow rate in vehicles per hour.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|SignsWarning||1|Type of warning sign.||openlabel-v2.shacl.ttl|
|OddScenery|openlabel_v2|longitudinalDownSlopeValue||1|Downward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
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
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrive"></a>MotionDrive||1|An activity where the subject vehicle is moving in the direction it is facing.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionacceleratevalue"></a>motionAccelerateValue||1|Rate of acceleration (ms⁻²).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionuturn"></a>MotionUTurn||1|Subject performs a turn resulting in heading in the opposite direction.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionreverse"></a>MotionReverse||1|An activity where the subject vehicle is moving in the opposite direction to which it is facing.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeleft"></a>MotionLaneChangeLeft||1|An activity where the subject vehicle is in a lane left of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnright"></a>MotionTurnRight||1|Subject exits the intersection on a road to the right of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaway"></a>MotionAway||1|An activity where the road user is further away from the object by the end.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionstop"></a>MotionStop||1|An activity where the road user is stationary.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-behaviourcommunication"></a>BehaviourCommunication|||Communication type of road user behaviour.||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiontowards"></a>MotionTowards||1|An activity where the road user is closer to the object by the end.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondrivevalue"></a>motionDriveValue||1|Speed (km/h).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondeceleratevalue"></a>motionDecelerateValue||1|Rate of deceleration (ms⁻²).||openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionrun"></a>MotionRun||1|Locomotion mode where at a specific point no foot touches the ground.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionlanechangeright"></a>MotionLaneChangeRight||1|An activity where the subject vehicle is in a lane right of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionwalk"></a>MotionWalk||1|Locomotion mode where at least one foot is always on the ground.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionslide"></a>MotionSlide||1|An activity where a pedestrian is slipping/sliding on the road.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturn"></a>MotionTurn||1|An activity where the road user changes their heading.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionovertake"></a>MotionOvertake||1|An activity where the subject starts behind and ends up in front by changing lanes.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionturnleft"></a>MotionTurnLeft||1|Subject exits the intersection on a road to the left of the original.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncross"></a>MotionCross||1|An activity where the trajectory of the road user crosses the trajectory of the object.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motiondecelerate"></a>MotionDecelerate||1|An activity where the road user decreases their velocity.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutout"></a>MotionCutOut||1|An activity where the object vehicle suddenly moves out of the lane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motioncutin"></a>MotionCutIn||1|An activity where the subject vehicle ends up directly in front of the object vehicle.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Behaviour|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-motionaccelerate"></a>MotionAccelerate||1|An activity where the road user increases their velocity.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ConnectivityPositioning||1|Type of positioning system.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|TrafficAgentType||1|Presence of a specified traffic agent type.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|HorizontalCurves||1|Presence of curved roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SceneryZone||1|Type of zone.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ParticulatesPollution||1|Presence of smoke or pollution particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ParticulatesDust||1|Presence of sand or dust particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LaneSpecificationLaneCount||1|Presence of a specified lane count.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DaySunElevation||1|Presence of a specified sun elevation above the horizon.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LongitudinalLevelPlane||1|Presence of a level longitudinal plane.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|IlluminationCloudiness||1|Presence of cloudiness.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DrivableAreaSurfaceFeature||1|Type of drivable area surface feature.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LaneSpecificationMarking||1|Presence of lane markings.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DrivableAreaType||1|Type of drivable area.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|trafficAgentTypeValue|||Types of traffic agents present.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ParticulatesWater||1|Presence of non-precipitating water droplets or ice crystals.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|illuminationCloudinessValue||1|Cloud cover in okta.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|HorizontalStraights||1|Presence of straight roadway geometry.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|trafficFlowRateValue||1|Traffic flow rate in vehicles per hour.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DaySunPosition||1|Position of the sun relative to the direction of travel.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LaneSpecificationType|||Type of lane.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|JunctionRoundabout||1|Type of roundabout.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|IlluminationLowLight||1|Type of low-light condition.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DrivableAreaEdge|||Type of drivable area edge.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ParticulatesMarine||1|Presence of marine spray in coastal areas.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SignsWarning||1|Type of warning sign.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|TrafficAgentDensity||1|Presence of a specified traffic agent density.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|longitudinalUpSlopeValue||1|Upward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DrivableAreaSurfaceCondition||1|Type of drivable area surface condition.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ParticulatesVolcanic||1|Presence of volcanic ash particulates.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|WeatherSnow||1|Presence of snowfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SignsInformation||1|Type of information sign.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|subjectVehicleSpeedValue||1|Subject vehicle speed in kilometres per hour.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|TrafficFlowRate||1|Presence of a specified traffic flow rate.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|TrafficSpecialVehicle||1|Presence of special vehicles.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|weatherRainValue||1|Rainfall intensity in millimetres per hour.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ConnectivityCommunication||1|Type of communication connectivity.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SceneryFixedStructure||1|Type of basic road structure present in the scenery.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|JunctionIntersection||1|Type of intersection.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|weatherSnowValue||1|Visibility in kilometres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|longitudinalDownSlopeValue||1|Downward gradient as a percentage.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|WeatherWind||1|Presence of wind.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LaneSpecificationTravelDirection||1|Direction of travel.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LongitudinalDownSlope||1|Presence of a downhill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|laneSpecificationDimensionsValue||1|Lane width in metres.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|DrivableAreaSurfaceType||1|Type of drivable area surface.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|daySunElevationValue||1|Sun elevation in degrees.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|particulatesWaterValue||1|Meteorological optical range in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|trafficAgentDensityValue||1|Traffic agent density in vehicles per kilometre.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LaneSpecificationDimensions||1|Presence of specified lane dimensions.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|RainType||1|Type of rainfall.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|laneSpecificationLaneCountValue||1|Number of lanes.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SubjectVehicleSpeed||1|Presence of a specified subject vehicle speed.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|TrafficVolume||1|Presence of a specified traffic volume.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|horizontalCurvesValue||1|Curve radius in metres.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SceneryTemporaryStructure||1|Type of temporary drivable area structure present in the scenery.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|SignsRegulatory||1|Type of regulatory sign.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|weatherWindValue||1|Wind speed in metres per second.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|WeatherRain||1|Presence of rainfall.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|EnvironmentParticulates||1|Type of particulates present in the environment.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|GeometryTransverse||1|Type of transverse geometry.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|trafficVolumeValue||1|Traffic volume in vehicle kilometres.|<http://www.w3.org/2001/XMLSchema#integer>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|ScenerySpecialStructure||1|Type of special structure present in the scenery.||openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|LongitudinalUpSlope||1|Presence of an uphill gradient.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|Odd|openlabel_v2|IlluminationArtificial||1|Type of artificial illumination.||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduservehicle"></a>RoadUserVehicle||1|Vehicle type.||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|motionDriveValue||1|Speed (km/h).||openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduseranimal"></a>RoadUserAnimal||1|Animal road user flag.|<http://www.w3.org/2001/XMLSchema#boolean>|openlabel-v2.shacl.ttl|
|RoadUser|openlabel_v2|<a id="prop-https---w3id-org-ascs-ev-envited-x-openlabel-v2-roaduserhuman"></a>RoadUserHuman||1|Human road user type.||openlabel-v2.shacl.ttl|
|QuantitativeValue|cmns-q|<a id="prop-https---www-omg-org-spec-commons-quantities-hasupperbound"></a>hasUpperBound||1|Upper bound inferred via RDFS from schema:maxValue being a subPropertyOf cmns-q:hasUpperBound in schema.org OWL.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|schema|<a id="prop-https---schema-org-minvalue"></a>minValue|1|1|Minimum value of the range.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|schema|<a id="prop-https---schema-org-maxvalue"></a>maxValue|1|1|Maximum value of the range.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
|QuantitativeValue|cmns-q|<a id="prop-https---www-omg-org-spec-commons-quantities-haslowerbound"></a>hasLowerBound||1|Lower bound inferred via RDFS from schema:minValue being a subPropertyOf cmns-q:hasLowerBound in schema.org OWL.|<http://www.w3.org/2001/XMLSchema#decimal>|openlabel-v2.shacl.ttl|
