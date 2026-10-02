## ositrace Properties

### Class Diagram

```mermaid
classDiagram
class ASAM_OSI_GroundTruth
class ASAM_OSI_HostVehicleData
class ASAM_OSI_MotionRequest
class ASAM_OSI_SensorData
class ASAM_OSI_SensorView
class ASAM_OSI_SensorViewConfiguration
class ASAM_OSI_StreamingUpdate
class ASAM_OSI_TrafficCommand
class ASAM_OSI_TrafficCommandUpdate
class ASAM_OSI_TrafficUpdate
class barrier
class bicycle
class bidirectional
class bike
class biking
class border
class building
class bus
class bus_1
class car
class Channel
class CompressionEnum
class connectingRamp
class Content
class crosswalk
class curb
class DataSource
class detection_list
class DomainSpecification
class driving
class entry
class Event
class exit
class FileFormatEnum
class Format
class FormatTypeEnum
class gantry
class GranularityEnum
class GroundTruth
class HostVehicleData
class HOV
class LaneTypesEnum
class left_hand
class LevelOfDetailEnum
class lowSpeed
class lz4
class MCAP
class median
class MessageTypeEnum
class MotionRequest
class motorbike
class motorway
class MovingObject
class mwyEntry
class mwyExit
class none
class none_1
class object_list
class obstacle
class offRamp
class onRamp
class OSI
class OSITrace
class parking
class parkingSpace
class patch
class pedestrian
class pedestrian_1
class pole
class Quality
class Quantity
class rail
class railing
class raw_data
class restricted
class right_hand
class roadMark
class roadSurface
class RoadTypesEnum
class roadWorks
class rural
class SensorData
class SensorView
class SensorViewConfiguration
class shared
class shoulder
class sidewalk
class slipLane
class soundBarrier
class special1
class special2
class special3
class stop
class StreamingUpdate
class streetLamp
class taxi
class town
class townArterial
class townCollector
class townExpressway
class townLocal
class townPlayStreet
class townPrivate
class TrafficCommand
class TrafficCommandUpdate
class TrafficDirectionEnum
class trafficIsland
class TrafficUpdate
class trailer
class train
class tram
class tram_1
class tree
class truck
class TXTH
class uncompressed
class unknown
class van
class vegetation
class walking
class wind
class zstd
CompressionEnum <|-- lz4
CompressionEnum <|-- uncompressed
CompressionEnum <|-- zstd
FileFormatEnum <|-- MCAP
FileFormatEnum <|-- OSI
FileFormatEnum <|-- TXTH
FormatTypeEnum <|-- ASAM_OSI_GroundTruth
FormatTypeEnum <|-- ASAM_OSI_HostVehicleData
FormatTypeEnum <|-- ASAM_OSI_MotionRequest
FormatTypeEnum <|-- ASAM_OSI_SensorData
FormatTypeEnum <|-- ASAM_OSI_SensorView
FormatTypeEnum <|-- ASAM_OSI_SensorViewConfiguration
FormatTypeEnum <|-- ASAM_OSI_StreamingUpdate
FormatTypeEnum <|-- ASAM_OSI_TrafficCommand
FormatTypeEnum <|-- ASAM_OSI_TrafficCommandUpdate
FormatTypeEnum <|-- ASAM_OSI_TrafficUpdate
GranularityEnum <|-- detection_list
GranularityEnum <|-- object_list
GranularityEnum <|-- raw_data
LaneTypesEnum <|-- HOV
LaneTypesEnum <|-- bidirectional
LaneTypesEnum <|-- biking
LaneTypesEnum <|-- border
LaneTypesEnum <|-- bus
LaneTypesEnum <|-- connectingRamp
LaneTypesEnum <|-- curb
LaneTypesEnum <|-- driving
LaneTypesEnum <|-- entry
LaneTypesEnum <|-- exit
LaneTypesEnum <|-- median
LaneTypesEnum <|-- mwyEntry
LaneTypesEnum <|-- mwyExit
LaneTypesEnum <|-- none
LaneTypesEnum <|-- offRamp
LaneTypesEnum <|-- onRamp
LaneTypesEnum <|-- parking
LaneTypesEnum <|-- rail
LaneTypesEnum <|-- restricted
LaneTypesEnum <|-- roadWorks
LaneTypesEnum <|-- shared
LaneTypesEnum <|-- shoulder
LaneTypesEnum <|-- sidewalk
LaneTypesEnum <|-- slipLane
LaneTypesEnum <|-- special1
LaneTypesEnum <|-- special2
LaneTypesEnum <|-- special3
LaneTypesEnum <|-- stop
LaneTypesEnum <|-- taxi
LaneTypesEnum <|-- tram
LaneTypesEnum <|-- walking
LevelOfDetailEnum <|-- barrier
LevelOfDetailEnum <|-- bike
LevelOfDetailEnum <|-- building
LevelOfDetailEnum <|-- bus_1
LevelOfDetailEnum <|-- car
LevelOfDetailEnum <|-- crosswalk
LevelOfDetailEnum <|-- gantry
LevelOfDetailEnum <|-- motorbike
LevelOfDetailEnum <|-- none_1
LevelOfDetailEnum <|-- obstacle
LevelOfDetailEnum <|-- parkingSpace
LevelOfDetailEnum <|-- patch
LevelOfDetailEnum <|-- pedestrian
LevelOfDetailEnum <|-- pole
LevelOfDetailEnum <|-- railing
LevelOfDetailEnum <|-- roadMark
LevelOfDetailEnum <|-- roadSurface
LevelOfDetailEnum <|-- soundBarrier
LevelOfDetailEnum <|-- streetLamp
LevelOfDetailEnum <|-- trafficIsland
LevelOfDetailEnum <|-- trailer
LevelOfDetailEnum <|-- train
LevelOfDetailEnum <|-- tram_1
LevelOfDetailEnum <|-- tree
LevelOfDetailEnum <|-- truck
LevelOfDetailEnum <|-- van
LevelOfDetailEnum <|-- vegetation
LevelOfDetailEnum <|-- wind
MessageTypeEnum <|-- GroundTruth
MessageTypeEnum <|-- HostVehicleData
MessageTypeEnum <|-- MotionRequest
MessageTypeEnum <|-- SensorData
MessageTypeEnum <|-- SensorView
MessageTypeEnum <|-- SensorViewConfiguration
MessageTypeEnum <|-- StreamingUpdate
MessageTypeEnum <|-- TrafficCommand
MessageTypeEnum <|-- TrafficCommandUpdate
MessageTypeEnum <|-- TrafficUpdate
RoadTypesEnum <|-- bicycle
RoadTypesEnum <|-- lowSpeed
RoadTypesEnum <|-- motorway
RoadTypesEnum <|-- pedestrian_1
RoadTypesEnum <|-- rural
RoadTypesEnum <|-- town
RoadTypesEnum <|-- townArterial
RoadTypesEnum <|-- townCollector
RoadTypesEnum <|-- townExpressway
RoadTypesEnum <|-- townLocal
RoadTypesEnum <|-- townPlayStreet
RoadTypesEnum <|-- townPrivate
RoadTypesEnum <|-- unknown
TrafficDirectionEnum <|-- left_hand
TrafficDirectionEnum <|-- right_hand
```

### Class Hierarchy

- Channel (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Channel)
- CompressionEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum)
  - lz4 (https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#lz4)
  - uncompressed (https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#uncompressed)
  - zstd (https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#zstd)
- Content (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Content)
- DataSource (https://w3id.org/ascs-ev/envited-x/ositrace/v7/DataSource)
- DomainSpecification (https://w3id.org/ascs-ev/envited-x/ositrace/v7/DomainSpecification)
- Event (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Event)
- FileFormatEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum)
  - MCAP (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#MCAP)
  - OSI (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#OSI)
  - TXTH (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#TXTH)
- Format (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Format)
- FormatTypeEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum)
  - ASAM OSI GroundTruth (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20GroundTruth)
  - ASAM OSI HostVehicleData (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20HostVehicleData)
  - ASAM OSI MotionRequest (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20MotionRequest)
  - ASAM OSI SensorData (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorData)
  - ASAM OSI SensorView (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorView)
  - ASAM OSI SensorViewConfiguration (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorViewConfiguration)
  - ASAM OSI StreamingUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20StreamingUpdate)
  - ASAM OSI TrafficCommand (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficCommand)
  - ASAM OSI TrafficCommandUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficCommandUpdate)
  - ASAM OSI TrafficUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficUpdate)
- GranularityEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum)
  - detection list (https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#detection%20list)
  - object list (https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#object%20list)
  - raw data (https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#raw%20data)
- LaneTypesEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum)
  - bidirectional (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#bidirectional)
  - biking (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#biking)
  - border (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#border)
  - bus (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#bus)
  - connectingRamp (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#connectingRamp)
  - curb (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#curb)
  - driving (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#driving)
  - entry (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#entry)
  - exit (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#exit)
  - HOV (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#HOV)
  - median (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#median)
  - mwyEntry (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#mwyEntry)
  - mwyExit (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#mwyExit)
  - none (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#none)
  - offRamp (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#offRamp)
  - onRamp (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#onRamp)
  - parking (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#parking)
  - rail (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#rail)
  - restricted (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#restricted)
  - roadWorks (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#roadWorks)
  - shared (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#shared)
  - shoulder (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#shoulder)
  - sidewalk (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#sidewalk)
  - slipLane (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#slipLane)
  - special1 (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special1)
  - special2 (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special2)
  - special3 (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special3)
  - stop (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#stop)
  - taxi (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#taxi)
  - tram (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#tram)
  - walking (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#walking)
- LevelOfDetailEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum)
  - barrier (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#barrier)
  - bike (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#bike)
  - building (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#building)
  - bus (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#bus)
  - car (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#car)
  - crosswalk (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#crosswalk)
  - gantry (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#gantry)
  - motorbike (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#motorbike)
  - none (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#none)
  - obstacle (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#obstacle)
  - parkingSpace (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#parkingSpace)
  - patch (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#patch)
  - pedestrian (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#pedestrian)
  - pole (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#pole)
  - railing (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#railing)
  - roadMark (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#roadMark)
  - roadSurface (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#roadSurface)
  - soundBarrier (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#soundBarrier)
  - streetLamp (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#streetLamp)
  - trafficIsland (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#trafficIsland)
  - trailer (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#trailer)
  - train (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#train)
  - tram (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#tram)
  - tree (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#tree)
  - truck (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#truck)
  - van (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#van)
  - vegetation (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#vegetation)
  - wind (https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#wind)
- MessageTypeEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum)
  - GroundTruth (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#GroundTruth)
  - HostVehicleData (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#HostVehicleData)
  - MotionRequest (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#MotionRequest)
  - SensorData (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorData)
  - SensorView (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorView)
  - SensorViewConfiguration (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorViewConfiguration)
  - StreamingUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#StreamingUpdate)
  - TrafficCommand (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficCommand)
  - TrafficCommandUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficCommandUpdate)
  - TrafficUpdate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficUpdate)
- MovingObject (https://w3id.org/ascs-ev/envited-x/ositrace/v7/MovingObject)
- OSITrace (https://w3id.org/ascs-ev/envited-x/ositrace/v7/OSITrace)
- Quality (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Quality)
- Quantity (https://w3id.org/ascs-ev/envited-x/ositrace/v7/Quantity)
- RoadTypesEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum)
  - bicycle (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#bicycle)
  - lowSpeed (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#lowSpeed)
  - motorway (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#motorway)
  - pedestrian (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#pedestrian)
  - rural (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#rural)
  - town (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#town)
  - townArterial (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townArterial)
  - townCollector (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townCollector)
  - townExpressway (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townExpressway)
  - townLocal (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townLocal)
  - townPlayStreet (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townPlayStreet)
  - townPrivate (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townPrivate)
  - unknown (https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#unknown)
- TrafficDirectionEnum (https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum)
  - left-hand (https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum#left-hand)
  - right-hand (https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum#right-hand)

### Class Definitions

|Class|IRI|Description|Parents|
|---|---|---|---|
|ASAM OSI GroundTruth|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20GroundTruth||FormatTypeEnum|
|ASAM OSI HostVehicleData|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20HostVehicleData||FormatTypeEnum|
|ASAM OSI MotionRequest|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20MotionRequest||FormatTypeEnum|
|ASAM OSI SensorData|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorData||FormatTypeEnum|
|ASAM OSI SensorView|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorView||FormatTypeEnum|
|ASAM OSI SensorViewConfiguration|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20SensorViewConfiguration||FormatTypeEnum|
|ASAM OSI StreamingUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20StreamingUpdate||FormatTypeEnum|
|ASAM OSI TrafficCommand|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficCommand||FormatTypeEnum|
|ASAM OSI TrafficCommandUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficCommandUpdate||FormatTypeEnum|
|ASAM OSI TrafficUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum#ASAM%20OSI%20TrafficUpdate||FormatTypeEnum|
|barrier|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#barrier||LevelOfDetailEnum|
|bicycle|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#bicycle||RoadTypesEnum|
|bidirectional|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#bidirectional||LaneTypesEnum|
|bike|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#bike||LevelOfDetailEnum|
|biking|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#biking||LaneTypesEnum|
|border|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#border||LaneTypesEnum|
|building|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#building||LevelOfDetailEnum|
|bus|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#bus||LaneTypesEnum|
|bus|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#bus||LevelOfDetailEnum|
|car|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#car||LevelOfDetailEnum|
|Channel|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Channel|Represents a single channel in an MCAP container file. Each channel carries messages of one OSI top-level type at a specific OSI schema version. Linked from ositrace:Format via ositrace:hasChannel.||
|CompressionEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum|||
|connectingRamp|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#connectingRamp||LaneTypesEnum|
|Content|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Content|Attributes for the content of ASAM OSI trace files.|Content|
|crosswalk|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#crosswalk||LevelOfDetailEnum|
|curb|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#curb||LaneTypesEnum|
|DataSource|https://w3id.org/ascs-ev/envited-x/ositrace/v7/DataSource|Attributes for the data source of ASAM OSI trace files.|DataSource|
|detection list|https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#detection%20list||GranularityEnum|
|DomainSpecification|https://w3id.org/ascs-ev/envited-x/ositrace/v7/DomainSpecification|OSI trace DomainSpecification containing additional metadata information of the simulation asset.|DomainSpecification|
|driving|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#driving||LaneTypesEnum|
|entry|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#entry||LaneTypesEnum|
|Event|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Event|Attributes for event in ASAM OSI trace files.||
|exit|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#exit||LaneTypesEnum|
|FileFormatEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum|||
|Format|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Format|Attributes for the format of ASAM OSI trace files, covering both single-channel .osi files and multi-channel MCAP containers.|Format|
|FormatTypeEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FormatTypeEnum|||
|gantry|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#gantry||LevelOfDetailEnum|
|GranularityEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum|||
|GroundTruth|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#GroundTruth||MessageTypeEnum|
|HostVehicleData|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#HostVehicleData||MessageTypeEnum|
|HOV|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#HOV||LaneTypesEnum|
|LaneTypesEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum|||
|left-hand|https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum#left-hand||TrafficDirectionEnum|
|LevelOfDetailEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum|||
|lowSpeed|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#lowSpeed||RoadTypesEnum|
|lz4|https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#lz4||CompressionEnum|
|MCAP|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#MCAP||FileFormatEnum|
|median|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#median||LaneTypesEnum|
|MessageTypeEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum|||
|MotionRequest|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#MotionRequest||MessageTypeEnum|
|motorbike|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#motorbike||LevelOfDetailEnum|
|motorway|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#motorway||RoadTypesEnum|
|MovingObject|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MovingObject|Attributes for moving objects in ASAM OSI trace files.||
|mwyEntry|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#mwyEntry||LaneTypesEnum|
|mwyExit|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#mwyExit||LaneTypesEnum|
|none|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#none||LaneTypesEnum|
|none|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#none||LevelOfDetailEnum|
|object list|https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#object%20list||GranularityEnum|
|obstacle|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#obstacle||LevelOfDetailEnum|
|offRamp|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#offRamp||LaneTypesEnum|
|onRamp|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#onRamp||LaneTypesEnum|
|OSI|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#OSI||FileFormatEnum|
|OSITrace|https://w3id.org/ascs-ev/envited-x/ositrace/v7/OSITrace|Attributes for ASAM OSI trace files.|SimulationAsset|
|parking|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#parking||LaneTypesEnum|
|parkingSpace|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#parkingSpace||LevelOfDetailEnum|
|patch|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#patch||LevelOfDetailEnum|
|pedestrian|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#pedestrian||LevelOfDetailEnum|
|pedestrian|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#pedestrian||RoadTypesEnum|
|pole|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#pole||LevelOfDetailEnum|
|Quality|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Quality|Attributes for the quality of ASAM OSI trace files.|Quality|
|Quantity|https://w3id.org/ascs-ev/envited-x/ositrace/v7/Quantity|Attributes for the quantity of ASAM OSI trace files.|Quantity|
|rail|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#rail||LaneTypesEnum|
|railing|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#railing||LevelOfDetailEnum|
|raw data|https://w3id.org/ascs-ev/envited-x/ositrace/v7/GranularityEnum#raw%20data||GranularityEnum|
|restricted|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#restricted||LaneTypesEnum|
|right-hand|https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum#right-hand||TrafficDirectionEnum|
|roadMark|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#roadMark||LevelOfDetailEnum|
|roadSurface|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#roadSurface||LevelOfDetailEnum|
|RoadTypesEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum|||
|roadWorks|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#roadWorks||LaneTypesEnum|
|rural|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#rural||RoadTypesEnum|
|SensorData|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorData||MessageTypeEnum|
|SensorView|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorView||MessageTypeEnum|
|SensorViewConfiguration|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#SensorViewConfiguration||MessageTypeEnum|
|shared|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#shared||LaneTypesEnum|
|shoulder|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#shoulder||LaneTypesEnum|
|sidewalk|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#sidewalk||LaneTypesEnum|
|slipLane|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#slipLane||LaneTypesEnum|
|soundBarrier|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#soundBarrier||LevelOfDetailEnum|
|special1|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special1||LaneTypesEnum|
|special2|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special2||LaneTypesEnum|
|special3|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#special3||LaneTypesEnum|
|stop|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#stop||LaneTypesEnum|
|StreamingUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#StreamingUpdate||MessageTypeEnum|
|streetLamp|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#streetLamp||LevelOfDetailEnum|
|taxi|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#taxi||LaneTypesEnum|
|town|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#town||RoadTypesEnum|
|townArterial|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townArterial||RoadTypesEnum|
|townCollector|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townCollector||RoadTypesEnum|
|townExpressway|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townExpressway||RoadTypesEnum|
|townLocal|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townLocal||RoadTypesEnum|
|townPlayStreet|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townPlayStreet||RoadTypesEnum|
|townPrivate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#townPrivate||RoadTypesEnum|
|TrafficCommand|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficCommand||MessageTypeEnum|
|TrafficCommandUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficCommandUpdate||MessageTypeEnum|
|TrafficDirectionEnum|https://w3id.org/ascs-ev/envited-x/ositrace/v7/TrafficDirectionEnum|||
|trafficIsland|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#trafficIsland||LevelOfDetailEnum|
|TrafficUpdate|https://w3id.org/ascs-ev/envited-x/ositrace/v7/MessageTypeEnum#TrafficUpdate||MessageTypeEnum|
|trailer|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#trailer||LevelOfDetailEnum|
|train|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#train||LevelOfDetailEnum|
|tram|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#tram||LaneTypesEnum|
|tram|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#tram||LevelOfDetailEnum|
|tree|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#tree||LevelOfDetailEnum|
|truck|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#truck||LevelOfDetailEnum|
|TXTH|https://w3id.org/ascs-ev/envited-x/ositrace/v7/FileFormatEnum#TXTH||FileFormatEnum|
|uncompressed|https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#uncompressed||CompressionEnum|
|unknown|https://w3id.org/ascs-ev/envited-x/ositrace/v7/RoadTypesEnum#unknown||RoadTypesEnum|
|van|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#van||LevelOfDetailEnum|
|vegetation|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#vegetation||LevelOfDetailEnum|
|walking|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LaneTypesEnum#walking||LaneTypesEnum|
|wind|https://w3id.org/ascs-ev/envited-x/ositrace/v7/LevelOfDetailEnum#wind||LevelOfDetailEnum|
|zstd|https://w3id.org/ascs-ev/envited-x/ositrace/v7/CompressionEnum#zstd||CompressionEnum|

## Prefixes

- envited-x: <https://w3id.org/ascs-ev/envited-x/envited-x/v4/>
- envitedx_ontology: <https://w3id.org/ascs-ev/envited-x/envited-x/>
- georeference: <https://w3id.org/ascs-ev/envited-x/georeference/v6/>
- georeference_ontology: <https://w3id.org/ascs-ev/envited-x/georeference/>
- manifest: <https://w3id.org/ascs-ev/envited-x/manifest/v6/>
- ositrace: <https://w3id.org/ascs-ev/envited-x/ositrace/v7/>
- rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
- rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- sh: <http://www.w3.org/ns/shacl#>
- xsd: <http://www.w3.org/2001/XMLSchema#>

### SHACL Properties

#### envited-x:hasContent {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hascontent .property-anchor }
#### envited-x:hasDataSource {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasdatasource .property-anchor }
#### envited-x:hasDomainSpecification {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasdomainspecification .property-anchor }
#### envited-x:hasFormat {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasformat .property-anchor }
#### envited-x:hasManifest {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasmanifest .property-anchor }
#### envited-x:hasQuality {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasquality .property-anchor }
#### envited-x:hasQuantity {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasquantity .property-anchor }
#### envited-x:hasResourceDescription {: #prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasresourcedescription .property-anchor }
#### ositrace:accuracyLaneModel2d {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracylanemodel2d .property-anchor }
#### ositrace:accuracyLaneModelHeight {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracylanemodelheight .property-anchor }
#### ositrace:accuracyObjects {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracyobjects .property-anchor }
#### ositrace:accuracySignals {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracysignals .property-anchor }
#### ositrace:calibration {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-calibration .property-anchor }
#### ositrace:compression {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-compression .property-anchor }
#### ositrace:description {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-description .property-anchor }
#### ositrace:fileFormat {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-fileformat .property-anchor }
#### ositrace:formatType {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-formattype .property-anchor }
#### ositrace:granularity {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-granularity .property-anchor }
#### ositrace:hasChannel {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-haschannel .property-anchor }
#### ositrace:hasContent {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hascontent .property-anchor }
#### ositrace:hasDataSource {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasdatasource .property-anchor }
#### ositrace:hasDomainSpecification {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasdomainspecification .property-anchor }
#### ositrace:hasEvent {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasevent .property-anchor }
#### ositrace:hasFormat {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasformat .property-anchor }
#### ositrace:hasGeoreference {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasgeoreference .property-anchor }
#### ositrace:hasHostMovingObject {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hashostmovingobject .property-anchor }
#### ositrace:hasManifest {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasmanifest .property-anchor }
#### ositrace:hasQuality {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasquality .property-anchor }
#### ositrace:hasQuantity {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasquantity .property-anchor }
#### ositrace:hasResourceDescription {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasresourcedescription .property-anchor }
#### ositrace:hasTargetMovingObject {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hastargetmovingobject .property-anchor }
#### ositrace:identifier {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-identifier .property-anchor }
#### ositrace:laneTypes {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-lanetypes .property-anchor }
#### ositrace:levelOfDetail {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-levelofdetail .property-anchor }
#### ositrace:maxOsiVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-maxosiversion .property-anchor }
#### ositrace:maxProtobufVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-maxprotobufversion .property-anchor }
#### ositrace:measurementSystem {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-measurementsystem .property-anchor }
#### ositrace:messageType {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-messagetype .property-anchor }
#### ositrace:minOsiVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-minosiversion .property-anchor }
#### ositrace:minProtobufVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-minprotobufversion .property-anchor }
#### ositrace:numberFrames {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberframes .property-anchor }
#### ositrace:numberOfChannels {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberofchannels .property-anchor }
#### ositrace:numberOfMessages {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberofmessages .property-anchor }
#### ositrace:osiTraceFormatVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-ositraceformatversion .property-anchor }
#### ositrace:osiVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-osiversion .property-anchor }
#### ositrace:precision {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-precision .property-anchor }
#### ositrace:protobufVersion {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-protobufversion .property-anchor }
#### ositrace:roadTypes {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-roadtypes .property-anchor }
#### ositrace:scenarioIdentifier {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-scenarioidentifier .property-anchor }
#### ositrace:startTime {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-starttime .property-anchor }
#### ositrace:stopTime {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-stoptime .property-anchor }
#### ositrace:tag {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-tag .property-anchor }
#### ositrace:time {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-time .property-anchor }
#### ositrace:topic {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-topic .property-anchor }
#### ositrace:trafficDirection {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-trafficdirection .property-anchor }
#### ositrace:usedDataSources {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-useddatasources .property-anchor }
#### ositrace:validationReport {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-validationreport .property-anchor }
#### ositrace:validationReportType {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-validationreporttype .property-anchor }
#### ositrace:version {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-version .property-anchor }
#### ositrace:zeroTime {: #prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-zerotime .property-anchor }

|Shape|Property prefix|Property|MinCount|MaxCount|Description|Datatype/NodeKind|Filename|
|---|---|---|---|---|---|---|---|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberofmessages"></a>numberOfMessages||1|Number of messages in this channel.|<http://www.w3.org/2001/XMLSchema#integer>|ositrace.shacl.ttl|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-osiversion"></a>osiVersion|1|1|OSI schema version used by this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-messagetype"></a>messageType|1|1|OSI top-level message type carried by this channel. Same ten ASAM OSI v3.8.0 types as ositrace:formatType on ositrace:SingleChannelFormatShape, in the bare lexical form: formatType == 'ASAM OSI ' + messageType.||ositrace.shacl.ttl|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-protobufversion"></a>protobufVersion||1|Protobuf version used for serialization in this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-description"></a>description||1|Human-readable description of this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|ChannelShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-topic"></a>topic|1|1|Unique MCAP topic name identifying this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-levelofdetail"></a>levelOfDetail|||Covered object classes. Complete ASAM OpenDRIVE e_objectType enumeration (27 values) as defined in submodules/asam-openx-standards/standards/asam-opendrive/schema/OpenDRIVE_Object.xsd (ASAM OpenDRIVE V1.9.0) and specified in ASAM OpenDRIVE v1.9.0 §13 'Objects', plus 'truck', which is not an e_objectType in any schema pinned by this repository and is carried as an ENVITED-X ecosystem extension for parity with hdmap:DomainSpecificationShape. Deprecated by ASAM OpenDRIVE V1.9.0 and accepted here only so that existing assets stay valid: 'patch' (use 'roadSurface'), 'railing' and 'soundBarrier' (use 'barrier'), 'streetLamp' and 'wind' (use 'pole'), and 'car', 'bus', 'trailer', 'bike', 'motorbike', 'tram', 'train', 'pedestrian' with no replacement named - describe traffic participants as ositrace:MovingObject instead. Prefer the non-deprecated values in new self-descriptions.||ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-lanetypes"></a>laneTypes|||Covered lane types. Complete ASAM OpenDRIVE e_laneType enumeration (31 values) as defined in submodules/asam-openx-standards/standards/asam-opendrive/schema/OpenDRIVE_Lane.xsd (ASAM OpenDRIVE V1.9.0) and specified in ASAM OpenDRIVE v1.9.0 §11.8 'Additional lane properties'. Identical to the v1.8+ branch enforced on hdmap:DomainSpecificationShape. Deprecated by ASAM OpenDRIVE V1.9.0 and accepted here only so that existing assets stay valid: 'sidewalk' (use 'walking'), 'bus' and 'taxi' (use the lane <access> element), 'mwyEntry' (use 'entry'), 'mwyExit' (use 'exit'), and 'special1', 'special2', 'special3' with no replacement named. 'bidirectional' is deprecated by the v1.9.0 specification §11.8 in favour of the lane @direction attribute, but is not marked deprecated in the schema. Prefer the non-deprecated spellings in new self-descriptions.||ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasevent"></a>hasEvent|||Description of events of interest in trace file.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-granularity"></a>granularity|1||Level of granularity of the trace content, aligned with what the ASAM OSI top-level message types carry: 'object list' for GroundTruth and for the DetectedMovingObject/DetectedStationaryObject lists of SensorData; 'detection list' for the SensorData FeatureData detections; 'raw data' for the unprocessed sensor input of SensorView (radar and lidar Reflection lists, camera image data, ultrasonic). Without 'raw data' a SensorView trace cannot satisfy this mandatory property. See ASAM OSI v3.8.0 osi_sensorview.proto, osi_sensordata.proto and osi_groundtruth.proto, pinned at submodules/asam-openx-standards/submodules/open-simulation-interface.||ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-starttime"></a>startTime|1|1|Exact start timestamp of the recorded trace|<http://www.w3.org/2001/XMLSchema#dateTime>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hastargetmovingobject"></a>hasTargetMovingObject|||Target moving object(s) in trace file.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-trafficdirection"></a>trafficDirection||1|Traffic direction, i.e. right-hand or left-hand traffic||ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-roadtypes"></a>roadTypes|||Covered/used road types, defined over the ASAM OpenDRIVE element t_road_type. Complete e_roadType enumeration (13 values) as defined in submodules/asam-openx-standards/standards/asam-opendrive/schema/OpenDRIVE_Road.xsd (ASAM OpenDRIVE V1.9.0) and specified in ASAM OpenDRIVE v1.9.0 §10.4 'Road type'. No e_roadType value is deprecated.||ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hashostmovingobject"></a>hasHostMovingObject|1|1|Host moving object in trace file.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-scenarioidentifier"></a>scenarioIdentifier|||Identifier of scenario performed in the trace file|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|ContentShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-stoptime"></a>stopTime|1|1|Exact stop timestamp of the recorded trace|<http://www.w3.org/2001/XMLSchema#dateTime>|ositrace.shacl.ttl|
|DataSourceShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-measurementsystem"></a>measurementSystem||1|Main acquisition device|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|DataSourceShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-useddatasources"></a>usedDataSources|||Basic data for the creation of the trace.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|DomainSpecificationShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasformat"></a>hasFormat|||Links a DomainSpecification to the format details of the asset.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hascontent"></a>hasContent|1|1|Attributes describing the content of the OSI trace.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasquality"></a>hasQuality||1|Links a DomainSpecification to the quality or accuracy aspects of the asset.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasgeoreference"></a>hasGeoreference||1|Links an OSI trace DomainSpecification to its georeferencing information.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasquantity"></a>hasQuantity||1|Links a DomainSpecification to the quantity of the asset.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasquantity"></a>hasQuantity|1|1|Quantitative metrics describing the OSI trace.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasdatasource"></a>hasDataSource|1|1|Data sources used to create the OSI trace.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasquality"></a>hasQuality|1|1|Quality metrics of the OSI trace.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasdatasource"></a>hasDataSource||1|Links a DomainSpecification to how the asset was created.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasformat"></a>hasFormat|1|1|File format details of the OSI trace.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|DomainSpecificationShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hascontent"></a>hasContent|1||Links a DomainSpecification to the content of the asset.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|EventShape|ositrace|description||1|Human-readable description of this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|EventShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-tag"></a>tag|1|1|Unique tag of the event in trace file.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|EventShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-time"></a>time|1|1|Exact timestamp of the event in the recorded trace.|<http://www.w3.org/2001/XMLSchema#dateTime>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-maxprotobufversion"></a>maxProtobufVersion||1|Maximum protobuf version across all channels.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-haschannel"></a>hasChannel|||Channels in the MCAP container. Each channel carries messages of one OSI top-level type.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-minosiversion"></a>minOsiVersion||1|Minimum OSI schema version across all channels.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-ositraceformatversion"></a>osiTraceFormatVersion||1|MCAP metadata record name identifying the file as an OSI trace (always 'net.asam.osi.trace').|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-zerotime"></a>zeroTime||1|Zero-time reference point for the MCAP recording.|<http://www.w3.org/2001/XMLSchema#dateTime>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-minprotobufversion"></a>minProtobufVersion||1|Minimum protobuf version across all channels.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-version"></a>version||1|Version of data format (OSI version / protobuf version).|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-fileformat"></a>fileFormat||1|Serialization of the single-channel trace file, per ASAM OSI v3.8.0 'OSI trace file formats' section 'Single channel trace file formats': 'OSI' for the binary .osi format (messages prefixed by a four-byte little-endian unsigned length), 'TXTH' for the human-readable .txth format (protocol buffer text format, newline-separated). Not required, so single-channel self-descriptions that omit it stay valid; but because this shape is sh:closed false the property was previously accepted with any value, so declaring it outside {OSI, TXTH} is now a violation. The multi-channel counterpart is the mandatory 'MCAP' discriminator on ositrace:MultiChannelFormatShape.||ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-compression"></a>compression||1|MCAP chunk compression algorithm.||ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-formattype"></a>formatType||1|Top-level OSI message type carried by the trace file. Complete set of the ten single-channel trace file types enumerated in ASAM OSI v3.8.0 'OSI trace file naming conventions' (sv, svc, gt, hvd, sd, tc, tcu, tu, mr, su), pinned at submodules/asam-openx-standards/submodules/open-simulation-interface. This property and ositrace:messageType on ositrace:ChannelShape model the same ten OSI types in two lexical forms: formatType == 'ASAM OSI ' + messageType. Unifying them would invalidate existing self-descriptions, so both spellings are kept; a future major version should collapse them.||ositrace.shacl.ttl|
|FormatShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-maxosiversion"></a>maxOsiVersion||1|Maximum OSI schema version across all channels.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|MovingObjectShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-identifier"></a>identifier|1|1|Moving object identifier in trace file.|<http://www.w3.org/2001/XMLSchema#integer>|ositrace.shacl.ttl|
|MovingObjectShape|ositrace|description||1|Human-readable description of this channel.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|OSITraceShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasresourcedescription"></a>hasResourceDescription|1|1|Links an asset or its subclass to its associated ResourceDescription, which provides essential metadata such as name and description, inline or as a link.||ositrace.shacl.ttl|
|OSITraceShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasdomainspecification"></a>hasDomainSpecification|||Links an asset to one or more metadata extensions (e.g., georeference metadata, sensor calibration) that provide additional structured information.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|OSITraceShape|envited-x|<a id="prop-https---w3id-org-ascs-ev-envited-x-envited-x-v4-hasmanifest"></a>hasManifest|1|1|Links an asset to its manifest: an inline envited-x:Manifest, or a link that names an external manifest by its IRI, typically a DID.||ositrace.shacl.ttl|
|OSITraceShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasresourcedescription"></a>hasResourceDescription|1|1|Links an OSI trace asset to a standard ResourceDescription instance from envited-x.||ositrace.shacl.ttl|
|OSITraceShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasmanifest"></a>hasManifest|1|1|Links an OSI Trace asset to its manifest: an inline envited-x:Manifest, or a manifest:Link pointing to an external manifest representation.||ositrace.shacl.ttl|
|OSITraceShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-hasdomainspecification"></a>hasDomainSpecification|1|1|Links an OSI trace asset to its specific metadata (DomainSpecification), which may contain additional OSI trace-specific attributes.|<http://www.w3.org/ns/shacl#BlankNodeOrIRI>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracylanemodelheight"></a>accuracyLaneModelHeight||1|Accuracy lane modell height|<http://www.w3.org/2001/XMLSchema#float>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracylanemodel2d"></a>accuracyLaneModel2d||1|Accuracy of lane modell 2d.|<http://www.w3.org/2001/XMLSchema#float>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-precision"></a>precision||1|Precision of measured road network (relative accuracy).|<http://www.w3.org/2001/XMLSchema#float>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-validationreport"></a>validationReport||1|Link to OSI trace file validation report, if any exists. The report should be of type 'vv-report:VvReport' according to https://w3id.org/gaia-x4plcaad/ontologies/vv-report/v2.|<http://www.w3.org/2001/XMLSchema#anyURI>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracyobjects"></a>accuracyObjects||1|Accuracy of objects in the traffic space, which do not directly affect the traffic.|<http://www.w3.org/2001/XMLSchema#float>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-calibration"></a>calibration||1|Description of any calibration steps performed prior to measurement.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-accuracysignals"></a>accuracySignals||1|Accuracy of traffic relevant objects, signs and signals.|<http://www.w3.org/2001/XMLSchema#float>|ositrace.shacl.ttl|
|QualityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-validationreporttype"></a>validationReportType||1|Type of OSI trace validation report, if any exists. As mime-type.|<http://www.w3.org/2001/XMLSchema#string>|ositrace.shacl.ttl|
|QuantityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberofchannels"></a>numberOfChannels||1|Number of channels in the MCAP container (MCAP files only).|<http://www.w3.org/2001/XMLSchema#integer>|ositrace.shacl.ttl|
|QuantityShape|ositrace|<a id="prop-https---w3id-org-ascs-ev-envited-x-ositrace-v7-numberframes"></a>numberFrames||1|Number of frames/messages in the trace file. For MCAP files, this is the total across all channels.|<http://www.w3.org/2001/XMLSchema#integer>|ositrace.shacl.ttl|
