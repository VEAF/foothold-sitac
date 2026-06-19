# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Foothold Sitac is a web application that displays tactical maps (sitac) for DCS World Foothold missions. It reads Lua persistence files from DCS Saved Games directories and renders zone/player data on interactive Leaflet maps.

## Commands

```bash
# Install dependencies
poetry install --only main

# Run the web server
poetry run python run.py

# Run tests
poetry run pytest

# Run a single test
poetry run pytest tests/units/test_foothold.py::test_zone_hidden_true -v

# Run linting (ruff + mypy strict)
./scripts/lint.sh
```

## Configuration

Copy `config/config.yml.dist` to `config/config.yml` and update values. The config supports environment variable expansion (e.g., `${VAR}`).

Key config sections:
- `web`: Server host, port, title, reload setting
- `dcs.saved_games`: Path to DCS Saved Games directory containing server folders
- `map`: Tile layer URLs, zoom levels, alternative tile layers

## Architecture

### Data Flow

1. DCS Foothold missions write Lua persistence files to `{saved_games}/{server}/Missions/Saves/`
2. `foothold.status` file in each server's Saves folder points to the active mission Lua file
3. `load_sitac()` parses Lua files using lupa (Lua runtime) into Pydantic models
4. FastAPI endpoints serve the data as JSON or render HTML templates with Leaflet maps

### Key Components

- **src/foothold_sitac/foothold.py**: Core domain logic - Lua parsing, Pydantic models (Zone, Sitac, Position, PlayerStats), server discovery functions
- **src/foothold_sitac/config.py**: YAML config loading with env var expansion, cached via `get_config()`
- **src/foothold_sitac/dependencies.py**: FastAPI dependency injection for loading sitac by server name
- **src/foothold_sitac/foothold_api_router.py**: REST API endpoints under `/api/foothold`
- **src/foothold_sitac/foothold_router.py**: HTML page routes under `/foothold`
- **src/foothold_sitac/templater.py**: Jinja2 environment setup with config globals
- **src/foothold_sitac/templates/**: Jinja2 HTML templates for map and server list pages
- **src/foothold_sitac/static/**: CSS, JS, and favicon assets
- **run.py**: Standalone script to launch the application

### Pydantic Models

- `Sitac`: Root model with zones dict, player stats, and update timestamp
- `Zone`: Zone state including side (1=red, 2=blue), level, units, position, hidden flag
- `MapData`/`MapZone`: Simplified API response schemas for map rendering

### Server Detection

The app auto-discovers Foothold servers by scanning `dcs.saved_games` for directories containing a `foothold.status` file in their `Missions/Saves/` subfolder.

### CTLD FARPs and DCS Coordinate Conversion

CTLD (Combat Troop and Logistics Delivery) writes FARP positions to CSV files (`{mission_name}_CTLD_FARPS.csv`). `load_farps()` in `foothold.py` supports two CSV layouts and inspects the first line to choose one:

- **New format (preferred)**: a column header containing `latitude`/`longitude` (e.g. `seq;name;x;y;zell;latitude;longitude;`). Coordinates are read straight from those columns — **no theater and no projection are needed**, so FARPs load even on theaters we cannot auto-detect.
- **Legacy format (fallback)**: a `FARP COORDINATES` title line followed by positional `seq;name;x;z` rows in DCS internal coordinates (x=north, z=east in meters). These are converted to lat/lon via a Transverse Mercator inverse projection, which requires a detected theater. When the theater is unknown, legacy rows cannot be converted and are skipped.

The conversion logic (fallback path only) is in `src/foothold_sitac/dcs_coordinates.py`. Each DCS map is a standard Transverse Mercator (`+proj=tmerc +lat_0=0 +k_0=0.9996`) and only three constants change per map (`lon_0`, `x_0`=false easting, `y_0`=false northing). These are **vendored verbatim** into the `THEATERS` table from the authoritative dataset at https://github.com/VEAF/dcs-maps (`exports/maps.yaml`), giving a near-exact conversion. To add or refresh a map: copy its `lon_0`/`x_0`/`y_0` from `maps.yaml` into `THEATERS` and add a detection bounding box.

**Theater detection hack**: Since the Lua persistence file does not contain the DCS theater name, the theater is detected by checking if the center of all zone lat/lon coordinates falls within a known geographic bounding box. This is fragile — geographically overlapping maps (e.g. Sinai/Syria, Normandy/TheChannel, Marianas/MarianasWWII) resolve by dict order. With the new CSV format this only affects the legacy fallback (new-format FARPs no longer depend on it).

Theaters supported by the legacy fallback (12): persianGulf, caucasus, syria, sinai, southAtlantic (Falklands), normandy, afghanistan, germanyCW, nevada, theChannel, marianaIslands, marianaIslandsWWII. **iraq** and **kola** are not yet in VEAF/dcs-maps, so legacy CSVs on those two maps remain unsupported until added upstream — but new-format CSVs (with lat/lon columns) work everywhere regardless.

## Documentation

- **docs/features.md**: Complete list of user-facing features (map, ruler, modals, API endpoints)
- **docs/lua-file-format.md**: Lua persistence file format documentation (Foothold 3.2.2) with YAML example
