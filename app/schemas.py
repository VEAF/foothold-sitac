from pydantic import BaseModel


class Server(BaseModel):
    name: str


class MapZone(BaseModel):

    name: str
    lat: float
    lon: float
    side: str
    color: str
