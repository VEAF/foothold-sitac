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
    refresh_interval: int = 60


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


def _expand_env_vars(value: Any) -> Any:
    """Recursively expand environment vars like "${VAR}" or "$VAR"."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    return value


def load_config_str(raw_config: dict[Any, Any]) -> AppConfig:
    expanded = _expand_env_vars(raw_config)
    return AppConfig.model_validate(expanded)


def load_config(path: str) -> AppConfig:
    with open(path, "r") as f:
        raw_config = yaml.safe_load(f)

    return load_config_str(raw_config)


@cache
def get_config() -> AppConfig:
    config_path = "config/config.yml"
    if not os.path.exists(config_path):
        return AppConfig(web=WebConfig(), dcs=DcsConfig(), map=MapConfig(alternative_tiles=[]))
    return load_config(config_path)
