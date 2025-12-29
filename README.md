# Foothold Sitac

POC about a web sitac for Foothold missions

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
poetry run python -m app.main
```

## Update

### Windows

Run `update.cmd`

### Linux/Mac

```shell
git pull origin main
poetry install --only main
```

## Run tests

```shell
poetry run pytest
```

## Access to web service

Default configuration: [localhost](http://localhost:8080)
