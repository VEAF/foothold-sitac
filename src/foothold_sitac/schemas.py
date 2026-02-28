from datetime import datetime
from pydantic import BaseModel, Field


class Server(BaseModel):
    name: str


<<<<<<< HEAD:app/schemas.py
class MapZoneGroupStatusEntry(BaseModel):
    name: str
    kind: str
    damaged: bool | None = None
=======
class UnitGroup(BaseModel):
    group_id: int
    units: dict[str, int]
>>>>>>> 30b585546ff6bd18e859386b4ef82393cebe4273:src/foothold_sitac/schemas.py


class MapZone(BaseModel):
    name: str
    lat: float
    lon: float
    side: str
    color: str
    units: int
    level: int
    flavor_text: str | None = None
<<<<<<< HEAD:app/schemas.py
    group_status: list[MapZoneGroupStatusEntry] = Field(default_factory=list)
    group_status_max: int | None = None
=======
    upgrades_used: int = 0
    unit_groups: list[UnitGroup] | None = None
>>>>>>> 30b585546ff6bd18e859386b4ef82393cebe4273:src/foothold_sitac/schemas.py


class MapConnection(BaseModel):
    from_zone: str
    to_zone: str
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float
    color: str


class MapPlayer(BaseModel):
    player_name: str
    lat: float
    lon: float
    coalition: str
    unit_type: str
    color: str


class MapEjectedPilot(BaseModel):
    player_name: str
    lat: float
    lon: float
    altitude: float
    lost_credits: float


class MapData(BaseModel):
    updated_at: datetime
    age_seconds: float
    zones: list[MapZone]
    connections: list[MapConnection]
    players: list[MapPlayer] = Field(default_factory=list)
    ejected_pilots: list[MapEjectedPilot] = Field(default_factory=list)
    progress: float
    missions_count: int
    ejected_pilots_count: int = 0
    red_credits: float = 0
    blue_credits: float = 0
    show_zone_forces: bool = True
