from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from app.foothold import Sitac, get_sitac_center, list_servers
from app.templater import env
from app.dependencies import get_active_sitac

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def foothold_servers(request: Request) -> str:
    servers = list_servers()

    template = env.get_template("foothold/servers.html")
    return template.render(
        {
            "request": request,
            "servers": servers,
        }
    )


@router.get("/sitac/{server}", response_class=HTMLResponse)
async def foothold_sitac(request: Request, sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/sitac.html")
    return template.render(
        {
            "request": request,
            "sitac": sitac,
        }
    )


@router.get("/map/{server}", response_class=HTMLResponse)
async def foothold_map(request: Request, server: str, sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
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
