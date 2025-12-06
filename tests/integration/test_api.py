import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_config


@pytest.fixture
def client():
    get_config.cache_clear()
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_config(monkeypatch):
    monkeypatch.setattr("app.config.get_config", lambda: type("AppConfig", (), {
        "dcs": type("DcsConfig", (), {"saved_games": "tests/fixtures"})(),
        "web": type("WebConfig", (), {"title": "Test"})(),
        "map": type("MapConfig", (), {"url_tiles": "", "min_zoom": 8, "max_zoom": 11})(),
    })())
    monkeypatch.setattr("app.foothold.get_config", lambda: type("AppConfig", (), {
        "dcs": type("DcsConfig", (), {"saved_games": "tests/fixtures"})(),
    })())


def test_map_data_excludes_hidden_zones(client):
    response = client.get("/api/foothold/test_hidden/map.json")
    assert response.status_code == 200

    data = response.json()
    assert "updated_at" in data
    assert "age_seconds" in data
    assert "zones" in data

    zones = data["zones"]
    zone_names = [z["name"] for z in zones]

    assert "VisibleZone1" in zone_names
    assert "VisibleZone2" in zone_names
    assert "HiddenZone1" not in zone_names
    assert "HiddenZone2" not in zone_names
    assert len(zones) == 2


def test_sitac_includes_hidden_zones(client):
    response = client.get("/api/foothold/test_hidden/sitac")
    assert response.status_code == 200

    sitac = response.json()
    zones = sitac["zones"]

    assert "VisibleZone1" in zones
    assert "VisibleZone2" in zones
    assert "HiddenZone1" in zones
    assert "HiddenZone2" in zones
    assert len(zones) == 4


def test_sitac_hidden_field_values(client):
    response = client.get("/api/foothold/test_hidden/sitac")
    assert response.status_code == 200

    zones = response.json()["zones"]

    assert zones["VisibleZone1"]["hidden"] is False
    assert zones["VisibleZone2"]["hidden"] is False
    assert zones["HiddenZone1"]["hidden"] is True
    assert zones["HiddenZone2"]["hidden"] is True
