from datetime import datetime
from pydantic import BaseModel, Field


class Server(BaseModel):
    name: str
    # "foothold", or "veaf" for a VEAF dynamic campaign (`<server>@<campaign>`)
    kind: str = "foothold"


class UnitGroup(BaseModel):
    group_id: int
    units: dict[str, int]


class MapZone(BaseModel):
    name: str
    lat: float
    lon: float
    side: str
    color: str
    units: int
    level: int
    flavor_text: str | None = None
    upgrades_used: int = 0
    unit_groups: list[UnitGroup] | None = None
    # VEAF dynamic campaigns only (None for Foothold)
    kind: str | None = None
    waypoint: int | None = None
    garrison_total: int | None = None
    capture_side: str | None = None
    capture_seconds: float | None = None
    structures_standing: int | None = None
    structures_total: int | None = None
    awake: bool | None = None


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


class MapMission(BaseModel):
    title: str
    lat: float
    lon: float
    is_running: bool
    is_escort_mission: bool


class MapFarp(BaseModel):
    name: str
    lat: float
    lon: float


class MapConvoy(BaseModel):
    side: str
    color: str
    from_zone: str
    to_zone: str
    from_lat: float
    from_lon: float
    to_lat: float
    to_lon: float
    units: int


class MapData(BaseModel):
    updated_at: datetime
    age_seconds: float
    is_fresh: bool = True
    zones: list[MapZone]
    connections: list[MapConnection]
    players: list[MapPlayer] = Field(default_factory=list)
    ejected_pilots: list[MapEjectedPilot] = Field(default_factory=list)
    missions: list[MapMission] = Field(default_factory=list)
    farps: list[MapFarp] = Field(default_factory=list)
    progress: float
    missions_count: int
    ejected_pilots_count: int = 0
    red_credits: float = 0
    blue_credits: float = 0
    show_zone_forces: bool = True
    source: str = "foothold"
    convoys: list[MapConvoy] = Field(default_factory=list)
    red_resources: float | None = None
    blue_resources: float | None = None
