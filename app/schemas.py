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


class MapData(BaseModel):
    updated_at: datetime
    age_seconds: float
    zones: list[MapZone]
