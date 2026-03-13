# Foothold Lua Persistence File Format

This document describes the structure of the Lua persistence file written by DCS Foothold missions (version 3.2.2). The file contains the complete state of a Foothold campaign: zones, players, missions, connections, and statistics.

## File Location

Foothold missions write persistence files to:

```
{DCS Saved Games}/{server}/Missions/Saves/
```

A `foothold.status` file in the same directory contains the path to the active mission Lua file.

## Root Structure

The file defines a single global Lua table `zonePersistance` with the following top-level keys:

| Key | Type | Description |
|-----|------|-------------|
| `zones` | dict | All campaign zones keyed by zone name |
| `zonesDetails` | dict | Zone metadata (flavor text, hidden flag) keyed by zone name |
| `playerStats` | dict | Player statistics keyed by player name |
| `ejectedPilots` | list | Ejected pilots with positions and credits |
| `missions` | list | Active missions |
| `connections` | list | Supply connections between zones |
| `players` | list | Currently connected players |
| `accounts` | list | Coalition credits (index 1=red, 2=blue) |
| `shops` | list | Coalition shops (index 1=red, 2=blue) |
| `tankers` | dict | Tanker aircraft configuration keyed by callsign |
| `customFlags` | dict | Mission flags (mixed indexed and named keys) |
| `ewrsSettings` | dict | EWRS configuration (can be empty) |
| `difficultyModifier` | number | Difficulty modifier value |

## zones

Each entry in `zonePersistance['zones']` is keyed by zone name (string) and contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `side` | number | yes | Coalition: `0` = neutral, `1` = red, `2` = blue |
| `active` | boolean | yes | Whether the zone is active in the campaign |
| `level` | number | yes | Zone level (0 = uncaptured, 1+ = upgrade level) |
| `upgradesUsed` | number | yes | Total upgrades used |
| `upgradesUsedRed` | number | yes | Red upgrades used |
| `upgradesUsedBlue` | number | yes | Blue upgrades used |
| `logisticCenter` | boolean | yes | Whether zone has a logistic center |
| `firstCaptureByRed` | boolean | yes | Whether zone was first captured by red |
| `wasBlue` | boolean | yes | Whether zone was previously blue |
| `lat_long` | object | yes | Zone position (see below) |
| `remainingUnits` | dict | yes | Deployed units by group (see below) |
| `destroyed` | dict | yes | Destroyed units (can be empty) |
| `extraUpgrade` | dict | yes | Extra upgrade data (can be empty) |
| `triggers` | dict | yes | Mission triggers (`trigger_name` → value) |
| `randomUpgradesRed` | list | no | Available red upgrade template names |
| `randomUpgradesBlue` | list | no | Available blue upgrade template names |

### lat_long

| Field | Type | Description |
|-------|------|-------------|
| `latitude` | number | Latitude in decimal degrees |
| `longitude` | number | Longitude in decimal degrees |
| `altitude` | number | Altitude in meters |

### remainingUnits

Nested structure indexed by group ID (integer), where each group is indexed by slot (integer) mapping to a unit type name (string):

```lua
['remainingUnits'] = {
  [1] = {                    -- group 1
    [1] = "Soldier M4 GRG",  -- slot 1
    [2] = "Soldier M249",    -- slot 2
  },
  [2] = {                    -- group 2
    [1] = "M1A2C_SEP_V3",
    [2] = "M-2 Bradley",
  },
}
```

Groups can be empty tables `{}` when all units in that group have been destroyed.

## zonesDetails

Each entry in `zonePersistance['zonesDetails']` is keyed by zone name and contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `flavorText` | string | no | Display text (e.g. waypoint label like `"WPT 8"`) |
| `hidden` | boolean | yes | Whether the zone is hidden on the map |

These details are merged into the corresponding zone entry during parsing.

## playerStats

Each entry in `zonePersistance['playerStats']` is keyed by player name (string). All fields are optional and default to `0` when absent.

| Field | Type | Description |
|-------|------|-------------|
| `Points` | number | Total points earned (can be a decimal) |
| `Points spent` | number | Points spent on upgrades/purchases |
| `Deaths` | number | Total deaths |
| `Air` | number | Air-to-air kills |
| `SAM` | number | SAM/air defense kills |
| `Ground Units` | number | Ground unit kills |
| `Infantry` | number | Infantry kills |
| `Helo` | number | Helicopter kills |
| `Structure` | number | Structure kills |
| `Zone capture` | number | Zones captured |
| `Zone upgrade` | number | Zone upgrades performed |
| `CAS mission` | number | CAS missions completed |
| `CAP mission` | number | CAP missions completed |
| `Recon mission` | number | Recon missions completed |
| `Pilot Rescue` | number | Pilot rescues performed |
| `Flight time` | number | Flight time (in minutes) |
| `Warehouse delivery` | number | Warehouse deliveries completed |
| `Bomb runway` | number | Runway bombing missions completed |
| `Intercept cargo plane` | number | Cargo plane interceptions completed |

> **Note:** Other stat keys may appear depending on the mission configuration. The list above covers all keys observed in Foothold Caucasus v0.2.

## ejectedPilots

Each entry in `zonePersistance['ejectedPilots']` is an indexed table:

| Field | Type | Description |
|-------|------|-------------|
| `playerName` | string | Pilot name |
| `latitude` | number | Latitude in decimal degrees |
| `longitude` | number | Longitude in decimal degrees |
| `altitude` | number | Altitude in meters |
| `lostCredits` | number | Credits lost (0 if rescued) |

## missions

Each entry in `zonePersistance['missions']` is an indexed table:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Mission title |
| `description` | string | Mission description |
| `isEscortMission` | boolean | Whether this is an escort mission |
| `isRunning` | boolean | Whether the mission is currently active |

## connections

Each entry in `zonePersistance['connections']` is an indexed table:

| Field | Type | Description |
|-------|------|-------------|
| `from` | string | Source zone name |
| `to` | string | Destination zone name |

Connections represent the supply chain between zones.

## players

Each entry in `zonePersistance['players']` is an indexed table:

| Field | Type | Description |
|-------|------|-------------|
| `coalition` | string | `"blue"` or `"red"` |
| `unitType` | string | DCS unit type (e.g. `"F-16C_50"`) |
| `playerName` | string | Player name |
| `latitude` | number | Current latitude in decimal degrees |
| `longitude` | number | Current longitude in decimal degrees |
| `altitude` | number | Current altitude in meters |

## accounts

Indexed table with coalition credits:

| Index | Description |
|-------|-------------|
| `[1]` | Red coalition credits |
| `[2]` | Blue coalition credits |

## shops

Indexed table (1=red, 2=blue). Each coalition shop is a dict keyed by item name:

```lua
['shops'] = {
  [1] = {},                    -- red shop (empty)
  [2] = {                      -- blue shop
    ['dynamictexaco'] = { ['stock'] = 1 },
    ['gslot'] = { ['stock'] = 1 },
  },
}
```

Each shop item has a `stock` (number) field.

## tankers

Each entry in `zonePersistance['tankers']` is keyed by tanker callsign:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `heading` | number | yes | Heading in degrees |
| `leg` | number | yes | Leg length |
| `speed` | number | no | Speed in knots |
| `unlocked` | boolean | yes | Whether the tanker is unlocked |

## customFlags

Dict with mixed key types (indexed integers and named strings), all mapping to boolean values:

```lua
['customFlags'] = {
  [1] = true,
  ['kutaisicaptured'] = true,
  ['StrikeTarget1'] = true,
}
```

## ewrsSettings

EWRS (Early Warning Radar System) configuration table. Can be empty.

## difficultyModifier

A single number representing the campaign difficulty modifier (e.g. `0`).

## Minimal YAML Example

A minimal representation of the Lua data structure in YAML format:

```yaml
# Foothold Lua Persistence - Minimal YAML Representation (v3.2.2)

zones:
  Gudauta:
    side: 2                      # 0=neutral, 1=red, 2=blue
    active: true
    level: 2
    upgradesUsed: 0
    upgradesUsedRed: 0
    upgradesUsedBlue: 0
    logisticCenter: false
    firstCaptureByRed: true
    wasBlue: true
    lat_long:
      latitude: 43.118
      longitude: 40.572
      altitude: 0
    remainingUnits:
      1:                         # group 1
        1: "Soldier M4 GRG"
        2: "Soldier M249"
      2:                         # group 2
        1: "M1A2C_SEP_V3"
        2: "M-2 Bradley"
    destroyed: {}
    extraUpgrade: {}
    triggers:
      missioncompleted: 3

zonesDetails:
  Gudauta:
    flavorText: "WPT 8"
    hidden: false

playerStats:
  Mitch:
    Points: 2582
    Deaths: 2
    Air: 2
    Zone capture: 1
    Zone upgrade: 8
    Points spent: 1690
    Ground Units: 6
    CAP mission: 1
    Flight time: 46
    Warehouse delivery: 9

ejectedPilots:
  - playerName: "Unknown"
    latitude: 43.29
    longitude: 40.28
    altitude: 481.08
    lostCredits: 0

missions:
  - title: "Intercept Bombers"
    description: "Enemy bombers spotted north of Mineralnye"
    isEscortMission: false
    isRunning: true

connections:
  - from: "Blue Carrier"
    to: "Batumi"
  - from: "Batumi"
    to: "Kobuleti"

players:
  - coalition: "blue"
    unitType: "F-16C_50"
    playerName: "APOLLO 11 | Tomy10"
    latitude: 43.484
    longitude: 40.146
    altitude: 5326.43

accounts:
  - 0            # [1] red credits
  - 14524.5      # [2] blue credits

shops:
  - {}                           # [1] red shop (empty)
  - dynamictexaco:               # [2] blue shop
      stock: 1

tankers:
  texaco:
    heading: 45
    leg: 0
    speed: 286
    unlocked: false

customFlags:
  kutaisicaptured: true
  StrikeTarget1: true

ewrsSettings: {}

difficultyModifier: 0
```
