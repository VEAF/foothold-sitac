# Features

## Server List

- Auto-discovers Foothold servers from DCS Saved Games directory
- Displays server cards with last update timestamp
- Visual freshness indicators (fresh/stale/unknown)

## Interactive Map

### Map Display

- Leaflet-based interactive map
- Multiple tile layer options (configurable)
- Auto-centers on mission zones

### Zones

- Colored circles indicating faction (Red/Blue/Neutral)
- Circle size based on zone level
- Dashed lines showing supply connections between zones
- Zoom-responsive labels (icons at low zoom, full names at high zoom)
- Click zones for detailed info (name, coalition, coordinates, unit count)
- Detailed forces composition per group (unit types and counts)
- Upgrades used vs zone level display
- Forces display configurable via `features.show_zone_forces` (default: enabled)

### Players

- Real-time player positions with aircraft icons
- Player name and unit type displayed at high zoom levels
- Tooltips on hover

### Ejected Pilots

- Parachute icons for ejected pilots
- Color-coded by credits status (green = saved, orange = lost)
- Click for detailed coordinates and altitude

## Ruler Tool

- Toggle via "Ruler" button in navbar
- Click two points on the map to measure
- Displays:
  - Distance in kilometers and nautical miles
  - Bearing with cardinal direction (N, NE, E, etc.)
  - Estimated flight time based on cruise speed setting

## Coordinate Display

- Real-time cursor position at bottom-left of map
- Multiple format options:
  - DMS: N41°07'24.42"
  - DDM: N41°07.4070'
  - Decimal: 41.123456°
- Preference saved in browser

## Modals

### Rankings

- Player statistics sorted by points
- Columns: Rank, Player Name, Points, Deaths, Zone Captures, Zone Upgrades, Air Units, Ground Units

### Objectives

- Campaign progress bar with percentage
- Tabbed interface (Blue/Neutral/Red zones)
- Zone tables showing name, level, upgrades, active status

### Missions

- Active mission list
- Type (Escort/Attack), Status (Running/Stopped)
- Color-coded badges

### Ejected Pilots

- List of all ejected pilots
- Coordinates in selected format, altitude, credits status

### Settings

- Coordinate format selection
- Cruise speed for ruler (100-350 knots)

## SITAC Table View

- Alternative tabular view at `/foothold/sitac/{server}`
- Complete zone listing with all attributes
- Full player statistics table

## Data Freshness

- Bottom-left indicator showing data age
- Green (fresh): data < 90 seconds old
- Yellow (stale): data > 90 seconds old
- Red (offline): connection lost
- Auto-refresh every 30 seconds

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/foothold` | List all Foothold servers |
| `GET /api/foothold/{server}/sitac` | Full sitac data (zones, players, missions) |
| `GET /api/foothold/{server}/map.json` | Map-specific data for rendering |
