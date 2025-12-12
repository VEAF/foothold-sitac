# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Foothold Sitac is a web application that displays tactical maps (sitac) for DCS World Foothold missions. It reads Lua persistence files from DCS Saved Games directories and renders zone/player data on interactive Leaflet maps.

## Commands

```bash
# Install dependencies
poetry install --only main

# Run the web server
poetry run python -m app.main

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

- **app/foothold.py**: Core domain logic - Lua parsing, Pydantic models (Zone, Sitac, Position, PlayerStats), server discovery functions
- **app/config.py**: YAML config loading with env var expansion, cached via `get_config()`
- **app/dependencies.py**: FastAPI dependency injection for loading sitac by server name
- **app/foothold_api_router.py**: REST API endpoints under `/api/foothold`
- **app/foothold_router.py**: HTML page routes under `/foothold`
- **app/templater.py**: Jinja2 environment setup with config globals
- **templates/**: Jinja2 HTML templates for map and server list pages

### Pydantic Models

- `Sitac`: Root model with zones dict, player stats, and update timestamp
- `Zone`: Zone state including side (1=red, 2=blue), level, units, position, hidden flag
- `MapData`/`MapZone`: Simplified API response schemas for map rendering

### Server Detection

The app auto-discovers Foothold servers by scanning `dcs.saved_games` for directories containing a `foothold.status` file in their `Missions/Saves/` subfolder.
