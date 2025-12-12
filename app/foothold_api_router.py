from datetime import datetime
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from app.dependencies import get_active_sitac
from app.foothold import Sitac, list_servers
from app.schemas import MapData, MapZone, Server

router = APIRouter()


@router.get("", response_model=list[Server], description="List foothold servers")
async def foothold_list_servers() -> Any:
    return [Server.model_validate({"name": server}) for server in list_servers()]


@router.get("/{server}/sitac", response_model=Sitac)
async def foothold_get_sitac(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> Any:
    return sitac


@router.get("/{server}/map.json", response_model=MapData)
async def foothold_get_map_data(
    sitac: Annotated[Sitac, Depends(get_active_sitac)],
) -> Any:
    zones = [
        MapZone.model_validate(
            {
                "name": zone_name,
                "lat": zone.position.latitude,
                "lon": zone.position.longitude,
                "side": zone.side_str,
                "color": zone.side_color,
                "units": zone.total_units,
                "level": zone.level,
            }
        )
        for zone_name, zone in sitac.zones.items()
        if zone.position and not zone.hidden
    ]

    age_seconds = (datetime.now() - sitac.updated_at).total_seconds()

    return MapData(updated_at=sitac.updated_at, age_seconds=age_seconds, zones=zones)
