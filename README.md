# Foothold Sitac

POC about a web sitac for Foothold missions

## Features

See [docs/features.md](docs/features.md) for a complete list of features including:
- Interactive tactical map with zone and player tracking
- Distance measurement tool (ruler)
- Player rankings and statistics
- Campaign progress tracking
- REST API for programmatic access

## Installation

### Prerequisites

- Git
- Python 3.12+
- Poetry

### Clone the project

```shell
git clone git@github.com:VEAF/foothold-sitac.git
cd foothold-sitac
```

### Windows (recommended)

1. Run `install.cmd` (copies config and installs dependencies)
2. Edit `config/config.yml` if needed (mandatory: set `dcs.saved_games` path)
3. Run `run.cmd` to start the web server

### Linux/Mac

1. Copy `config/config.yml.dist` to `config/config.yml`
2. Edit `config/config.yml` (mandatory: set `dcs.saved_games` path)
3. Install dependencies:
```shell
poetry install --only main
```
4. Start web service:
```shell
poetry run python run.py
```

## Update

### Windows

Run `update.cmd`

### Linux/Mac

```shell
git pull origin main
poetry install --only main
```

## Unit display names (optional)

To display human-readable unit names (on hover) instead of raw DCS type codes, set `dcs.install_path` in `config/config.yml` to your DCS World installation directory:

```yaml
dcs:
    install_path: "C:\\Program Files\\Eagle Dynamics\\DCS World"
```

Then extract the unit names:

```shell
poetry run foothold-sitac extract-unit-names
```

This generates `var/unit_display_names.json` (not versioned). If `dcs.install_path` is configured, the extraction also runs automatically at server startup.

You can also specify the path directly:

```shell
poetry run foothold-sitac extract-unit-names --dcs-path "C:\Program Files\Eagle Dynamics\DCS World"
```

## Run tests

```shell
poetry run pytest
```

## Access to web service

Default configuration: [localhost](http://localhost:8080)
