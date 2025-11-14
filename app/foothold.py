from datetime import datetime
from pathlib import Path
from lupa import LuaRuntime
from pydantic import BaseModel, Field
from app.config import get_config


class ConfigError(Exception):
    ...


class Position(BaseModel):
    latitude: float
    longitude: float
    altitude: int | None = None  # not used anymore


class Zone(BaseModel):
    upgrades_used: int = Field(alias="upgradesUsed")
    side: int
    active: bool
    destroyed: dict[int, str] | list[str] | dict
    extra_upgrade: dict = Field(alias="extraUpgrade")
    remaining_units: dict[int, dict[int, str]] | dict = Field(alias="remainingUnits")
    first_capture_by_red: bool = Field(alias="firstCaptureByRed")
    level: int
    wasBlue: bool
    triggers: dict[str, int]
    position: Position = Field(alias="lat_long")

    @property
    def side_color(self) -> str:
        if self.side == 1:
            return "red"
        elif self.side == 2:
            return "blue"
        return "lightgray"

    @property
    def side_str(self) -> str:
        if self.side == 1:
            return "red"
        elif self.side == 2:
            return "blue"
        return "neutral"

    @property
    def total_units(self) -> int:
        return sum([len(group_units) for group_units in self.remaining_units.values()])


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


class Sitac(BaseModel):
    updated_at: datetime
    zones: dict[str, Zone]
    player_stats: dict[str, PlayerStats] = Field(alias="playerStats")


def lua_to_dict(lua_table):
    if lua_table is None:
        return None
    result = {}
    for k, v in lua_table.items():
        if hasattr(v, "items"):
            v = lua_to_dict(v)
        result[k] = v
    return result


def load_sitac(file: Path) -> Sitac:

    lua = LuaRuntime(unpack_returned_tuples=True)

    with open(file.absolute(), "r", encoding="utf-8") as f:
        lua_code = f.read()

    lua.execute(lua_code)

    zone_persistance = lua.globals().zonePersistance  # type: ignore
    zone_persistance_dict = lua_to_dict(zone_persistance)

    return Sitac(
        **zone_persistance_dict,  # type: ignore
        updated_at=datetime.fromtimestamp(file.stat().st_mtime)
    )


def detect_foothold_mission_path(server_name: str) -> Path | None:

    file_status = get_foothold_server_status_path(server_name)

    if not file_status.is_file():
        return None

    with open(file_status) as f:
        mission_file_path = Path(f.readline().strip())

    print(mission_file_path)
    return mission_file_path


def get_server_path_by_name(server_name: str) -> Path:

    return Path(get_config().dcs.saved_games) / server_name


def get_foothold_server_saves_path(server_name: str) -> Path:

    return get_server_path_by_name(server_name) / "Missions" / "Saves"


def get_foothold_server_status_path(server_name: str) -> Path:

    return get_foothold_server_saves_path(server_name) / "foothold.status"


def is_foothold_path(server_name: str) -> bool:
    """Check if server_name (directory in DCS Saved Games) is a Foothold server path"""

    path = get_foothold_server_status_path(server_name)

    return path.is_file()


def list_servers() -> list[str]:

    base_path = Path(get_config().dcs.saved_games)

    if not base_path.is_dir():
        raise ConfigError(f"config:dcs.saved_games '{get_config().dcs.saved_games}' is not a valid dir")

    return sorted([
        file.name for file in base_path.iterdir()
        if not file.name.startswith(".") and is_foothold_path(file.name)
    ])


def get_sitac_range(sitac: Sitac) -> tuple[Position, Position]:

    if not sitac.zones:
        raise ValueError("sitac without zones")
    first_zone = sitac.zones[next(iter(sitac.zones))]

    min_lat, max_lat = first_zone.position.latitude, first_zone.position.latitude
    min_long, max_long = first_zone.position.longitude, first_zone.position.longitude

    for zone in sitac.zones.values():

        min_lat, max_lat = min(min_lat, zone.position.latitude), max(max_lat, zone.position.latitude)
        min_long, max_long = min(min_long, zone.position.longitude), max(max_long, zone.position.longitude)

    return Position(latitude=min_lat, longitude=min_long), Position(latitude=max_lat, longitude=max_long)


def get_sitac_center(sitac: Sitac) -> Position:

    min_pos, max_pos = get_sitac_range(sitac)

    return Position(
        latitude=(max_pos.latitude + min_pos.latitude)/2,
        longitude=(max_pos.longitude + min_pos.longitude)/2,
    )


if __name__ == "__main__":
    # only for debug
    test = load_sitac("var/footholdSyria_Extended_0.1.lua")
    print(test)
