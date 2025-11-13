from typing import Annotated
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from app.foothold import ZonePersistance, detect_foothold_mission_path, get_server_path_by_name, get_sitac_center, list_servers, load_sitac
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

router = APIRouter()


def get_active_sitac(server: str) -> ZonePersistance:
    """Dependency injection of sitac by server name"""

    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"server {server} not found")

    mission_path = detect_foothold_mission_path(server_path)

    if not mission_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"mission not found for server {server}")

    return load_sitac(mission_path)


@router.get("", response_class=HTMLResponse)
async def foothold_servers(request: Request):

    servers = list_servers()

    template = env.get_template("foothold/servers.html")
    return template.render(
        {
            "request": request,
            "servers": servers,
        }
    )


@router.get("/sitac/{server}", response_class=HTMLResponse)
async def foothold_sitac(request: Request, sitac: Annotated[ZonePersistance, Depends(get_active_sitac)]):

    template = env.get_template("foothold/sitac.html")
    return template.render(
        {
            "request": request,
            "sitac": sitac,
        }
    )


@router.get("/map/{server}", response_class=HTMLResponse)
async def foothold_map(request: Request, server: str, sitac: Annotated[ZonePersistance, Depends(get_active_sitac)]):

    template = env.get_template("foothold/map.html")
    map_center = get_sitac_center(sitac)

    return template.render(
        {
            "request": request,
            "sitac": sitac,
            "server": server,
            "center": [map_center.latitude, map_center.longitude],
        }
    )


@router.get("/map/{server}/data.json")
async def foothold_map_data(request: Request, sitac: Annotated[ZonePersistance, Depends(get_active_sitac)]):

    # sitac = load_sitac(FOOTHOLD_SITAC_PATH)  # todo use real data
    zones: list[dict[str, str | float]] = [
        {
            "name": zone_name,
            "lat": zone.position.latitude,
            "lon": zone.position.longitude,
            "side": zone.side_str,
            "color": zone.side_color
        }
        for zone_name, zone in sitac.zones.items() if zone.position
    ]

    return zones
