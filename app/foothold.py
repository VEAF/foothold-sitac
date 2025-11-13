import os
from pathlib import Path
from lupa import LuaRuntime
from pydantic import BaseModel, Field

DCS_SAVED_GAMES_PATH = os.getenv("DCS_SAVED_GAMES_PATH", "var")


class ConfigError(Exception):
    ...


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


def load_sitac(file: Path) -> ZonePersistance:

    lua = LuaRuntime(unpack_returned_tuples=True)

    with open(file.absolute(), "r", encoding="utf-8") as f:
        lua_code = f.read()

    lua.execute(lua_code)

    zone_persistance = lua.globals().zonePersistance  # type: ignore
    zone_persistance_dict = lua_to_dict(zone_persistance)

    return ZonePersistance(**zone_persistance_dict)  # type: ignore


def detect_foothold_mission_path(server_path: Path) -> Path | None:

    saves_path = server_path / "Missions" / "Saves"

    candidates: list[Path] = []

    if not saves_path.is_dir():
        raise ConfigError("not a foothold server")

    for file in saves_path.iterdir():
        if file.is_file() and file.name.endswith(".lua") and "_Extended_" in file.name:
            candidates.append(file)

    # no mission found ?
    if len(candidates) == 0:
        return None

    # newer is active mission
    return max(candidates, key=lambda f: f.stat().st_mtime)


def is_foothold_path(server_path: Path) -> bool:
    """Check if path is a Foothold server path

    Note: Foothold server should contain "Missions" subdirectory
    """

    missions_path = server_path / "Missions"

    return missions_path.is_dir()


def list_servers() -> list[str]:

    base_path = Path(DCS_SAVED_GAMES_PATH)

    if not base_path.is_dir():
        raise ConfigError(f"DCS_SAVED_GAMES_PATH '{DCS_SAVED_GAMES_PATH}' is not a valid dir")

    return sorted([
        file.name for file in base_path.iterdir()
        if is_foothold_path(file.absolute()) and not file.name.startswith(".")
    ])


def get_server_path_by_name(server: str) -> Path:

    return Path(DCS_SAVED_GAMES_PATH) / server


if __name__ == "__main__":
    # only for debug
    test = load_sitac("var/footholdSyria_Extended_0.1.lua")
    print(test)
