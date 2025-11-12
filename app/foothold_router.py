import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.foothold import load_sitac
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))

router = APIRouter()

FOOTHOLD_SITAC_PATH = os.getenv("FOOTHOLD_SITAC_PATH", "var/footholdSyria_Extended_0.1.lua")


@router.get("", response_class=HTMLResponse)
async def view_sitac(request: Request):

    sitac = load_sitac(FOOTHOLD_SITAC_PATH)

    template = env.get_template("sitac.html")
    return template.render(
        {
            "request": request,
            "sitac": sitac,
        }
    )
