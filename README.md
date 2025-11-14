# Foothold Sitac

POC about a web sitac for Foothold missions

## Work or install this project

```shell
git clone git@github.com:VEAF/foothold-sitac.git
cd foothold-sitac
```

- Copy app/config.yml.dist to app/config.yml
- Update app/config.yml values 
- install dependencies:
```shell
poetry install --only main
```
- start web service
```shell
poetry run python -m app.main
```

## Run tests

```shell
poetry run pytest
```

## Access to web service

Default configuration: [localhost](http://localhost:8080)
