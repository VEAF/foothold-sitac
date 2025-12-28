from datetime import datetime
from pydantic import BaseModel, Field


class Server(BaseModel):
    name: str


class MapZone(BaseModel):
    name: str
    lat: float
    lon: float
    side: str
    color: str
    units: int
    level: int
    flavor_text: str | None = None


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
