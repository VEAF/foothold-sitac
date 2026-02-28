from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from foothold_sitac.config import get_config
from foothold_sitac.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    get_config.cache_clear()
    yield TestClient(app)


@pytest.fixture(autouse=True)
def override_config(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_config = type(
        "AppConfig",
        (),
        {
            "dcs": type("DcsConfig", (), {"saved_games": "tests/fixtures"})(),
            "web": type("WebConfig", (), {"title": "Test"})(),
            "map": type("MapConfig", (), {"url_tiles": "", "min_zoom": 8, "max_zoom": 11})(),
            "features": type("FeaturesConfig", (), {"show_zone_forces": True})(),
        },
    )()
    monkeypatch.setattr("foothold_sitac.config.get_config", lambda: mock_config)
    monkeypatch.setattr(
        "foothold_sitac.foothold.get_config",
        lambda: type(
            "AppConfig",
            (),
            {
                "dcs": type("DcsConfig", (), {"saved_games": "tests/fixtures"})(),
            },
        )(),
    )


def test_map_data_excludes_hidden_zones(client: TestClient) -> None:
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


def test_sitac_includes_hidden_zones(client: TestClient) -> None:
    response = client.get("/api/foothold/test_hidden/sitac")
    assert response.status_code == 200

    sitac = response.json()
    zones = sitac["zones"]

    assert "VisibleZone1" in zones
    assert "VisibleZone2" in zones
    assert "HiddenZone1" in zones
    assert "HiddenZone2" in zones
    assert len(zones) == 4


def test_sitac_hidden_field_values(client: TestClient) -> None:
    response = client.get("/api/foothold/test_hidden/sitac")
    assert response.status_code == 200

    zones = response.json()["zones"]

    assert zones["VisibleZone1"]["hidden"] is False
    assert zones["VisibleZone2"]["hidden"] is False
    assert zones["HiddenZone1"]["hidden"] is True
    assert zones["HiddenZone2"]["hidden"] is True


# Missions tests


def test_sitac_includes_missions(client: TestClient) -> None:
    response = client.get("/api/foothold/test_missions/sitac")
    assert response.status_code == 200

    sitac = response.json()
    assert "missions" in sitac
    assert len(sitac["missions"]) == 2

    # Check first mission (JSON uses aliases: isEscortMission, isRunning)
    mission1 = sitac["missions"][0]
    assert mission1["title"] == "Attack Hahn (3)"
    assert mission1["description"] == "Destroy enemy forces at Hahn"
    assert mission1["isEscortMission"] is False
    assert mission1["isRunning"] is True

    # Check second mission (escort)
    mission2 = sitac["missions"][1]
    assert mission2["title"] == "Convoy Escort"
    assert mission2["isEscortMission"] is True
    assert mission2["isRunning"] is False


def test_sitac_without_missions_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/foothold/test_hidden/sitac")
    assert response.status_code == 200

    sitac = response.json()
    assert "missions" in sitac
    assert sitac["missions"] == []


def test_missions_modal_endpoint(client: TestClient) -> None:
    response = client.get("/foothold/map/test_missions/missions")
    assert response.status_code == 200
    assert "Attack Hahn (3)" in response.text
    assert "Convoy Escort" in response.text


# Accounts/credits tests


def test_map_data_includes_credits(client: TestClient) -> None:
    response = client.get("/api/foothold/test_accounts/map.json")
    assert response.status_code == 200

    data = response.json()
    assert data["red_credits"] == 736
    assert data["blue_credits"] == 33218


def test_map_data_credits_default_zero(client: TestClient) -> None:
    response = client.get("/api/foothold/test_missions/map.json")
    assert response.status_code == 200

    data = response.json()
    assert data["red_credits"] == 0
    assert data["blue_credits"] == 0


# Zone forces tests


def test_map_data_includes_unit_groups(client: TestClient) -> None:
    response = client.get("/api/foothold/test_forces/map.json")
    assert response.status_code == 200

    data = response.json()
    aleppo = next(z for z in data["zones"] if z["name"] == "Aleppo")
    assert aleppo["upgrades_used"] == 2
    assert aleppo["unit_groups"] is not None
    assert len(aleppo["unit_groups"]) == 2
    assert aleppo["unit_groups"][0]["group_id"] == 1
    assert aleppo["unit_groups"][0]["units"]["T-72B3"] == 2
    assert aleppo["unit_groups"][0]["units"]["BMP-1"] == 1
    assert aleppo["unit_groups"][1]["group_id"] == 2
    assert aleppo["unit_groups"][1]["units"]["SA-11 Buk CC 9S470M1"] == 1

    empty = next(z for z in data["zones"] if z["name"] == "EmptyZone")
    assert empty["unit_groups"] == []

    assert data["show_zone_forces"] is True


def test_map_data_includes_upgrades_used(client: TestClient) -> None:
    response = client.get("/api/foothold/test_forces/map.json")
    assert response.status_code == 200

    data = response.json()
    aleppo = next(z for z in data["zones"] if z["name"] == "Aleppo")
    assert aleppo["upgrades_used"] == 2
    assert aleppo["level"] == 3
