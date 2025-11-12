from lupa import LuaRuntime
from pydantic import BaseModel
from typing import Dict, List


class Zone(BaseModel):
    upgradesUsed: int
    side: int
    active: bool
    destroyed: Dict[int, str] | List[str] | dict
    extraUpgrade: dict
    remainingUnits: Dict[int, Dict[int, str]] | dict
    firstCaptureByRed: bool
    level: int
    wasBlue: bool
    triggers: Dict[str, int]


class PlayerStats(BaseModel):
    Air: int | None = 0
    SAM: int | None = 0
    Points: float | None = 0
    Deaths: int | None = 0
    Zone_capture: int | None = 0
    Zone_upgrade: int | None = 0
    CAS_mission: int | None = 0
    Points_spent: int | None = 0
    Infantry: int | None = 0
    Ground_Units: int | None = 0
    Helo: int | None = 0


class ZonePersistance(BaseModel):
    zones: Dict[str, Zone]
    playerStats: Dict[str, PlayerStats]


def lua_to_dict(lua_table):
    if lua_table is None:
        return None
    result = {}
    for k, v in lua_table.items():
        if hasattr(v, "items"):
            v = lua_to_dict(v)
        result[k] = v
    return result


def load_sitac(filename: str) -> ZonePersistance:

    lua = LuaRuntime(unpack_returned_tuples=True)

    with open(filename, "r", encoding="utf-8") as f:
        lua_code = f.read()

    lua.execute(lua_code)

    zone_persistance = lua.globals().zonePersistance  # type: ignore
    zone_persistance_dict = lua_to_dict(zone_persistance)

    return ZonePersistance(**zone_persistance_dict)  # type: ignore


if __name__ == "__main__":

    test = load_sitac("var/footholdSyria_Extended_0.1.lua")
    print(test)
