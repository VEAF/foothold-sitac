from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from app.foothold import detect_foothold_mission_path, get_server_path_by_name, list_servers, load_sitac
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

router = APIRouter()


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
async def foothold_sitac(request: Request, server: str):

    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"server {server} not found")

    mission_path = detect_foothold_mission_path(server_path)

    if not mission_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"mission not found for server {server}")

    sitac = load_sitac(mission_path)

    template = env.get_template("foothold/sitac.html")
    return template.render(
        {
            "request": request,
            "sitac": sitac,
        }
    )


@router.get("/ranking", response_class=HTMLResponse)
async def view_ranking(request: Request):

    raise Exception("TODO")
