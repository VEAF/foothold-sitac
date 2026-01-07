# test app/config.py

import tempfile
from typing import Any

import pytest
import yaml

from foothold_sitac.config import (
    AppConfig,
    TileLayerConfig,
    load_config,
    load_config_str,
)


def write_tmp_yaml(content: dict[str, Any]) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    with open(tmp.name, "w") as f:
        yaml.safe_dump(content, f)
    return tmp.name


@pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.1"])
@pytest.mark.parametrize("port", [80, 8080, 8081])
@pytest.mark.parametrize("title", ["Test Server", "VEAF SITAC"])
def test_load_config_str_basic(host: str, port: int, title: str) -> None:
    # GIVEN
    raw: dict[str, Any] = {
        "web": {
            "host": host,
            "port": port,
            "title": title,
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert isinstance(cfg, AppConfig)
    assert cfg.web.host == host
    assert cfg.web.port == port
    assert cfg.web.title == title


def test_load_config_str_defaults() -> None:
    # WHEN
    cfg = load_config_str({})

    # THEN
    assert cfg.web.host == "0.0.0.0"
    assert cfg.web.port == 8080
    assert cfg.web.title == "Foothold Sitac Server"


def test_load_config_str_env_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    # GIVEN
    monkeypatch.setenv("WEB_HOST", "10.0.0.5")
    monkeypatch.setenv("WEB_PORT", "7777")
    monkeypatch.setenv("WEB_TITLE", "My Sitac")

    raw = {
        "web": {
            "host": "${WEB_HOST}",
            "port": "$WEB_PORT",
            "title": "$WEB_TITLE",
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.web.host == "10.0.0.5"
    assert cfg.web.port == 7777
    assert cfg.web.title == "My Sitac"


def test_load_config_str_list_env_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    # GIVEN
    monkeypatch.setenv("A", "abc")
    monkeypatch.setenv("B", "def")

    raw: dict[str, Any] = {
        "web": {"title": "$A - ${B}"},
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.web.title == "abc - def"


def test_load_config_from_file() -> None:
    # GIVEN
    path = write_tmp_yaml(
        {
            "web": {
                "host": "1.2.3.4",
                "port": 8888,
                "title": "File Test",
            }
        }
    )

    # WHEN
    cfg = load_config(path)

    # THEN
    assert isinstance(cfg, AppConfig)
    assert cfg.web.host == "1.2.3.4"
    assert cfg.web.port == 8888
    assert cfg.web.title == "File Test"


# MapConfig tests


def test_map_config_defaults() -> None:
    # WHEN
    cfg = load_config_str({})

    # THEN
    assert (
        cfg.map.url_tiles
        == "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    )
    assert cfg.map.min_zoom == 8
    assert cfg.map.max_zoom == 11
    assert cfg.map.alternative_tiles == []


def test_map_config_custom_url_tiles() -> None:
    # GIVEN
    raw: dict[str, Any] = {
        "map": {
            "url_tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.map.url_tiles == "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


def test_map_config_alternative_tiles() -> None:
    # GIVEN
    raw: dict[str, Any] = {
        "map": {
            "alternative_tiles": [
                {
                    "name": "OpenStreetMap",
                    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                },
                {
                    "name": "Terrain",
                    "url": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
                },
            ]
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert len(cfg.map.alternative_tiles) == 2
    assert isinstance(cfg.map.alternative_tiles[0], TileLayerConfig)
    assert cfg.map.alternative_tiles[0].name == "OpenStreetMap"
    assert cfg.map.alternative_tiles[0].url == "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    assert cfg.map.alternative_tiles[1].name == "Terrain"
    assert cfg.map.alternative_tiles[1].url == "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg"


def test_map_config_alternative_tiles_empty() -> None:
    # GIVEN
    raw: dict[str, Any] = {"map": {"alternative_tiles": []}}

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.map.alternative_tiles == []


def test_map_config_alternative_tiles_env_expansion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # GIVEN
    monkeypatch.setenv("TILE_NAME", "Custom Map")
    monkeypatch.setenv("TILE_URL", "https://custom.tiles.org/{z}/{x}/{y}.png")

    raw: dict[str, Any] = {
        "map": {
            "alternative_tiles": [
                {"name": "$TILE_NAME", "url": "${TILE_URL}"},
            ]
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.map.alternative_tiles[0].name == "Custom Map"
    assert cfg.map.alternative_tiles[0].url == "https://custom.tiles.org/{z}/{x}/{y}.png"


def test_map_config_zoom_levels() -> None:
    # GIVEN
    raw: dict[str, Any] = {
        "map": {
            "min_zoom": 5,
            "max_zoom": 15,
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.map.min_zoom == 5
    assert cfg.map.max_zoom == 15


def test_map_config_full() -> None:
    # GIVEN
    raw = {
        "map": {
            "url_tiles": "https://custom.tiles.org/{z}/{x}/{y}.png",
            "min_zoom": 6,
            "max_zoom": 14,
            "alternative_tiles": [
                {
                    "name": "Satellite",
                    "url": "https://satellite.tiles.org/{z}/{x}/{y}.png",
                },
            ],
        }
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.map.url_tiles == "https://custom.tiles.org/{z}/{x}/{y}.png"
    assert cfg.map.min_zoom == 6
    assert cfg.map.max_zoom == 14
    assert len(cfg.map.alternative_tiles) == 1
    assert cfg.map.alternative_tiles[0].name == "Satellite"
