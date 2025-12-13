from pathlib import Path
from typing import Any

import pytest

from app.foothold import Connection, Mission, Zone, load_sitac


@pytest.fixture
def base_zone_data() -> dict[str, Any]:
    return {
        "upgradesUsed": 0,
        "side": 1,
        "active": True,
        "destroyed": {},
        "extraUpgrade": {},
        "remainingUnits": {},
        "firstCaptureByRed": True,
        "level": 1,
        "wasBlue": False,
        "triggers": {"missioncompleted": 0},
        "lat_long": {"latitude": 33.0, "longitude": 36.0, "altitude": 0},
    }


def test_zone_hidden_true(base_zone_data: dict[str, Any]) -> None:
    base_zone_data["hidden"] = True
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is True


def test_zone_hidden_false(base_zone_data: dict[str, Any]) -> None:
    base_zone_data["hidden"] = False
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is False


def test_zone_hidden_default(base_zone_data: dict[str, Any]) -> None:
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is False


def test_load_sitac_with_hidden_zones() -> None:
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    assert "VisibleZone1" in sitac.zones
    assert "VisibleZone2" in sitac.zones
    assert "HiddenZone1" in sitac.zones
    assert "HiddenZone2" in sitac.zones

    assert sitac.zones["VisibleZone1"].hidden is False
    assert sitac.zones["VisibleZone2"].hidden is False
    assert sitac.zones["HiddenZone1"].hidden is True
    assert sitac.zones["HiddenZone2"].hidden is True


def test_load_sitac_hidden_zones_count() -> None:
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    visible_zones = [z for z in sitac.zones.values() if not z.hidden]
    hidden_zones = [z for z in sitac.zones.values() if z.hidden]

    assert len(visible_zones) == 2
    assert len(hidden_zones) == 2


# Campaign progress tests


def test_sitac_campaign_progress_all_red() -> None:
    """100% rouge = 0% progression"""
    lua_path = Path("tests/fixtures/test_progress/foothold_all_red.lua")
    sitac = load_sitac(lua_path)
    assert sitac.campaign_progress == 0.0


def test_sitac_campaign_progress_all_blue() -> None:
    """100% bleu = 100% progression"""
    lua_path = Path("tests/fixtures/test_progress/foothold_all_blue.lua")
    sitac = load_sitac(lua_path)
    assert sitac.campaign_progress == 100.0


def test_sitac_campaign_progress_mixed() -> None:
    """2 rouges + 2 bleus = 50% progression"""
    lua_path = Path("tests/fixtures/test_progress/foothold_mixed.lua")
    sitac = load_sitac(lua_path)
    assert sitac.campaign_progress == 50.0


def test_sitac_campaign_progress_with_neutral() -> None:
    """Les zones neutres comptent comme non-rouges"""
    lua_path = Path("tests/fixtures/test_progress/foothold_with_neutral.lua")
    sitac = load_sitac(lua_path)
    # 1 rouge, 1 bleu, 1 neutre = (3-1)/3 = 66.67%
    assert sitac.campaign_progress == pytest.approx(66.67, rel=0.01)


def test_sitac_campaign_progress_excludes_hidden() -> None:
    """Les zones cachées sont exclues du calcul"""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)
    # Zones visibles: VisibleZone1 (rouge), VisibleZone2 (bleu)
    # = (2-1)/2 = 50%
    assert sitac.campaign_progress == 50.0


def test_sitac_campaign_progress_no_zones() -> None:
    """Sans zones, retourne 0"""
    lua_path = Path("tests/fixtures/test_progress/foothold_empty.lua")
    sitac = load_sitac(lua_path)
    assert sitac.campaign_progress == 0.0


# Mission tests


def test_mission_model_validation() -> None:
    """Test Mission model validation with valid data"""
    mission_data = {
        "isEscortMission": False,
        "description": "Destroy enemy forces at Hahn",
        "title": "Attack Hahn (3)",
        "isRunning": True,
    }
    mission = Mission.model_validate(mission_data)
    assert mission.is_escort_mission is False
    assert mission.description == "Destroy enemy forces at Hahn"
    assert mission.title == "Attack Hahn (3)"
    assert mission.is_running is True


def test_mission_escort_mission() -> None:
    """Test Mission model with escort mission"""
    mission_data = {
        "isEscortMission": True,
        "description": "Escort friendly convoy",
        "title": "Convoy Escort",
        "isRunning": False,
    }
    mission = Mission.model_validate(mission_data)
    assert mission.is_escort_mission is True
    assert mission.is_running is False


def test_load_sitac_with_missions() -> None:
    """Test loading sitac with missions"""
    lua_path = Path("tests/fixtures/test_missions/Missions/Saves/foothold_missions.lua")
    sitac = load_sitac(lua_path)

    assert len(sitac.missions) == 2
    assert sitac.missions[0].title == "Attack Hahn (3)"
    assert sitac.missions[0].is_running is True
    assert sitac.missions[0].is_escort_mission is False
    assert sitac.missions[1].title == "Convoy Escort"
    assert sitac.missions[1].is_escort_mission is True


def test_load_sitac_without_missions() -> None:
    """Test loading sitac without missions section (tolerance)"""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    # Should default to empty list
    assert sitac.missions == []


# FlavorText tests


def test_zone_flavor_text(base_zone_data: dict[str, Any]) -> None:
    """Test Zone model with flavorText"""
    base_zone_data["flavorText"] = "WPT 1"
    zone = Zone.model_validate(base_zone_data)
    assert zone.flavor_text == "WPT 1"


def test_zone_flavor_text_default(base_zone_data: dict[str, Any]) -> None:
    """Test Zone model without flavorText (default to None)"""
    zone = Zone.model_validate(base_zone_data)
    assert zone.flavor_text is None


def test_load_sitac_with_flavor_text() -> None:
    """Test loading sitac with flavorText"""
    lua_path = Path("tests/fixtures/test_missions/Missions/Saves/foothold_missions.lua")
    sitac = load_sitac(lua_path)

    assert sitac.zones["TestZone1"].flavor_text == "WPT 1"
    assert sitac.zones["TestZone2"].flavor_text == "WPT 2"
    assert sitac.zones["TestZone3"].flavor_text is None


# Connection tests


def test_connection_model_validation() -> None:
    """Test Connection model validation with valid data"""
    conn_data = {
        "from": "ZoneA",
        "to": "ZoneB",
    }
    conn = Connection.model_validate(conn_data)
    assert conn.from_zone == "ZoneA"
    assert conn.to_zone == "ZoneB"


def test_load_sitac_with_connections() -> None:
    """Test loading sitac with connections"""
    lua_path = Path("tests/fixtures/test_missions/Missions/Saves/foothold_missions.lua")
    sitac = load_sitac(lua_path)

    assert len(sitac.connections) == 2
    assert sitac.connections[0].from_zone == "TestZone1"
    assert sitac.connections[0].to_zone == "TestZone2"
    assert sitac.connections[1].from_zone == "TestZone2"
    assert sitac.connections[1].to_zone == "TestZone3"


def test_load_sitac_without_connections() -> None:
    """Test loading sitac without connections section (tolerance)"""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    # Should default to empty list
    assert sitac.connections == []
