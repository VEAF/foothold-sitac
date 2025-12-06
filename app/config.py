import os
from typing import Annotated, Any
from functools import cache
import yaml
from pydantic import BaseModel, Field


class WebConfig(BaseModel):

    host: str = "0.0.0.0"
    port: int = 8080
    title: str = "Foothold Sitac Server"
    reload: bool = False


class DcsConfig(BaseModel):

    saved_games: str = "var"  # "DCS Saved Games Path"


class TileLayerConfig(BaseModel):

    name: str
    url: str


class MapConfig(BaseModel):

    url_tiles: str = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    alternative_tiles: Annotated[list[TileLayerConfig], Field(default_factory=list)]

    min_zoom: int = 8
    max_zoom: int = 11


class AppConfig(BaseModel):

    web: Annotated[WebConfig, Field(default_factory=WebConfig)]
    dcs: Annotated[DcsConfig, Field(default_factory=DcsConfig)]
    map: Annotated[MapConfig, Field(default_factory=MapConfig)]


def load_config_str(raw_config: dict[Any, Any]) -> AppConfig:

    # Recursively expand environment vars like "${VAR}" or "$VAR"
    def expand(value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        if isinstance(value, list):
            return [expand(v) for v in value]
        return value

    expanded = expand(raw_config)
    return AppConfig.model_validate(expanded)


def load_config(path: str) -> AppConfig:
    with open(path, "r") as f:
        raw_config = yaml.safe_load(f)

    return load_config_str(raw_config)


@cache
def get_config() -> AppConfig:
    return load_config("config/config.yml")
