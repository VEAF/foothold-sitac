from pathlib import Path
from typing import Any

import pytest

from foothold_sitac.foothold import Connection, EjectedPilot, Mission, Player, Zone, load_sitac


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
    """Inactive neutral zones are excluded from progress calculation"""
    lua_path = Path("tests/fixtures/test_progress/foothold_with_neutral.lua")
    sitac = load_sitac(lua_path)
    # 1 red, 1 blue (inactive neutral excluded) = (2-1)/2 = 50%
    assert sitac.campaign_progress == 50.0


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


# Player tests


def test_player_model_validation() -> None:
    """Test Player model validation with valid data"""
    player_data = {
        "coalition": "blue",
        "unitType": "AH-64D_BLK_II",
        "playerName": "Ninja 1-1 | Zip",
        "latitude": 50.005976182135,
        "longitude": 8.0957305929501,
        "altitude": 85.99609375,
    }
    player = Player.model_validate(player_data)
    assert player.coalition == "blue"
    assert player.unit_type == "AH-64D_BLK_II"
    assert player.player_name == "Ninja 1-1 | Zip"
    assert player.latitude == 50.005976182135
    assert player.longitude == 8.0957305929501
    assert player.altitude == 85.99609375
    assert player.side_color == "blue"


def test_player_model_red_coalition() -> None:
    """Test Player model with red coalition"""
    player_data = {
        "coalition": "red",
        "unitType": "Su-25T",
        "playerName": "Red Pilot",
        "latitude": 51.0,
        "longitude": 9.0,
    }
    player = Player.model_validate(player_data)
    assert player.coalition == "red"
    assert player.side_color == "red"
    assert player.altitude is None


def test_player_model_unknown_coalition() -> None:
    """Test Player model with unknown coalition"""
    player_data = {
        "coalition": "neutral",
        "unitType": "C-130",
        "playerName": "Unknown",
        "latitude": 51.0,
        "longitude": 9.0,
    }
    player = Player.model_validate(player_data)
    assert player.side_color == "gray"


def test_load_sitac_with_players() -> None:
    """Test loading sitac with players"""
    lua_path = Path("var/test4/Missions/Saves/FootHold_Germany_Modern_V0.1.lua")
    sitac = load_sitac(lua_path)

    assert len(sitac.players) == 1
    assert sitac.players[0].player_name == "Ninja 1-1 | Zip"
    assert sitac.players[0].coalition == "blue"
    assert sitac.players[0].unit_type == "AH-64D_BLK_II"


def test_load_sitac_without_players() -> None:
    """Test loading sitac without players section (tolerance)"""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    # Should default to empty list
    assert sitac.players == []


# Ejected pilots tests


def test_ejected_pilot_model_validation() -> None:
    """Test EjectedPilot model validation with valid data"""
    pilot_data = {
        "playerName": "Unknown",
        "latitude": 52.850300007598,
        "longitude": 11.059029269508,
        "altitude": 49.431312561035,
        "lostCredits": 0,
    }
    pilot = EjectedPilot.model_validate(pilot_data)
    assert pilot.player_name == "Unknown"
    assert pilot.latitude == 52.850300007598
    assert pilot.longitude == 11.059029269508
    assert pilot.altitude == 49.431312561035
    assert pilot.lost_credits == 0


def test_ejected_pilot_model_with_credits() -> None:
    """Test EjectedPilot model with lost credits"""
    pilot_data = {
        "playerName": "Viper 1-1",
        "latitude": 50.0,
        "longitude": 10.0,
        "altitude": 100.0,
        "lostCredits": 500,
    }
    pilot = EjectedPilot.model_validate(pilot_data)
    assert pilot.player_name == "Viper 1-1"
    assert pilot.lost_credits == 500


def test_ejected_pilot_model_with_float_credits() -> None:
    """Test EjectedPilot model with float lost credits (DCS can send decimals)"""
    pilot_data = {
        "playerName": "Viper 1-1",
        "latitude": 50.0,
        "longitude": 10.0,
        "altitude": 100.0,
        "lostCredits": 337.5,
    }
    pilot = EjectedPilot.model_validate(pilot_data)
    assert pilot.player_name == "Viper 1-1"
    assert pilot.lost_credits == 337.5


def test_ejected_pilot_model_defaults() -> None:
    """Test EjectedPilot model with default values"""
    pilot_data = {
        "playerName": "Test Pilot",
        "latitude": 51.0,
        "longitude": 9.0,
    }
    pilot = EjectedPilot.model_validate(pilot_data)
    assert pilot.altitude == 0
    assert pilot.lost_credits == 0


def test_load_sitac_with_ejected_pilots() -> None:
    """Test loading sitac with ejected pilots"""
    lua_path = Path("tests/fixtures/test_ejected/Missions/Saves/foothold_ejected.lua")
    sitac = load_sitac(lua_path)

    assert len(sitac.ejected_pilots) == 3
    # All pilots have playerName "Unknown"
    assert all(p.player_name == "Unknown" for p in sitac.ejected_pilots)
    # Check that all expected latitudes are present (order may vary)
    latitudes = {p.latitude for p in sitac.ejected_pilots}
    assert 52.850300007598 in latitudes
    assert 52.903069323266 in latitudes
    assert 52.90260133955 in latitudes


def test_load_sitac_without_ejected_pilots() -> None:
    """Test loading sitac without ejectedPilots section (tolerance)"""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    # Should default to empty list
    assert sitac.ejected_pilots == []
