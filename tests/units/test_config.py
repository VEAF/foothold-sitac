# test app/config.py

import tempfile
import yaml
import pytest

from app.config import (
    load_config,
    load_config_str,
    AppConfig,
)


def write_tmp_yaml(content: dict) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
    with open(tmp.name, "w") as f:
        yaml.safe_dump(content, f)
    return tmp.name


@pytest.mark.parametrize("host", ["0.0.0.0", "127.0.0.1"])
@pytest.mark.parametrize("port", [80, 8080, 8081])
@pytest.mark.parametrize("title", ["Test Server", "VEAF SITAC"])
def test_load_config_str_basic(host: str, port: int, title: str):

    # GIVEN
    raw = {
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


def test_load_config_str_defaults():

    # WHEN
    cfg = load_config_str({})

    # THEN
    assert cfg.web.host == "0.0.0.0"
    assert cfg.web.port == 8080
    assert cfg.web.title == "Foothold Sitac Server"


def test_load_config_str_env_expansion(monkeypatch):

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


def test_load_config_str_list_env_expansion(monkeypatch):

    # GIVEN
    monkeypatch.setenv("A", "abc")
    monkeypatch.setenv("B", "def")

    raw = {
        "web": {"title": "$A - ${B}"},
    }

    # WHEN
    cfg = load_config_str(raw)

    # THEN
    assert cfg.web.title == "abc - def"


def test_load_config_from_file():

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
