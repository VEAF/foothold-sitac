from pathlib import Path
import pytest
from app.foothold import Zone, Position, load_sitac


@pytest.fixture
def base_zone_data():
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


def test_zone_hidden_true(base_zone_data):
    base_zone_data["hidden"] = True
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is True


def test_zone_hidden_false(base_zone_data):
    base_zone_data["hidden"] = False
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is False


def test_zone_hidden_default(base_zone_data):
    zone = Zone.model_validate(base_zone_data)
    assert zone.hidden is False


def test_load_sitac_with_hidden_zones():
    lua_path = Path("var/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    assert "VisibleZone1" in sitac.zones
    assert "VisibleZone2" in sitac.zones
    assert "HiddenZone1" in sitac.zones
    assert "HiddenZone2" in sitac.zones

    assert sitac.zones["VisibleZone1"].hidden is False
    assert sitac.zones["VisibleZone2"].hidden is False
    assert sitac.zones["HiddenZone1"].hidden is True
    assert sitac.zones["HiddenZone2"].hidden is True


def test_load_sitac_hidden_zones_count():
    lua_path = Path("var/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    sitac = load_sitac(lua_path)

    visible_zones = [z for z in sitac.zones.values() if not z.hidden]
    hidden_zones = [z for z in sitac.zones.values() if z.hidden]

    assert len(visible_zones) == 2
    assert len(hidden_zones) == 2
