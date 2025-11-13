# Foothold Sitac

POC about a web sitac for Foothold missions

## Work or install this project

Define an environment var DCS_SAVED_GAMES_PATH (ex: C:\Users\veaf\Saved Games)

```shell
git clone git@github.com:VEAF/foothold-sitac.git

cd foothold-sitac
poetry install
poetry run python -m app.main
```

## POC Notes

- need a file var/footholdSyria_Extended_0.1.lua to work
- service is exposed to http 8081 port
