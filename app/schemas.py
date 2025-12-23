from datetime import datetime
from pydantic import BaseModel


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


class MapData(BaseModel):
    updated_at: datetime
    age_seconds: float
    zones: list[MapZone]
    connections: list[MapConnection]
    players: list[MapPlayer] = []
    progress: float
    missions_count: int
