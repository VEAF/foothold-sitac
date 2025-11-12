from lupa import LuaRuntime
from pydantic import BaseModel, Field


class Zone(BaseModel):
    upgradesUsed: int
    side: int
    active: bool
    destroyed: dict[int, str] | list[str] | dict
    extraUpgrade: dict
    remainingUnits: dict[int, dict[int, str]] | dict
    firstCaptureByRed: bool
    level: int
    wasBlue: bool
    triggers: dict[str, int]


class PlayerStats(BaseModel):
    air: int = Field(alias="Air", default=0)
    SAM: int = Field(alias="SAM", default=0)
    points: float = Field(alias="Points", default=0)
    deaths: int = Field(alias="Deaths", default=0)
    zone_capture: int = Field(alias="Zone capture", default=0)
    zone_upgrade: int = Field(alias="Zone upgrade", default=0)
    CAS_mission: int = Field(alias="CAS mission", default=0)
    points_spent: int = Field(alias="Points spent", default=0)
    infantry: int = Field(alias="Infantry", default=0)
    ground_units: int = Field(alias="Ground Units", default=0)
    helo: int = Field(alias="Helo", default=0)


class ZonePersistance(BaseModel):
    zones: dict[str, Zone]
    playerStats: dict[str, PlayerStats]


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
