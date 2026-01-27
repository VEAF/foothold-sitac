from importlib.resources import files

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from foothold_sitac.briefing_api_router import router as briefing_api_router
from foothold_sitac.briefing_router import router as briefing_router
from foothold_sitac.config import get_config
from foothold_sitac.foothold_api_router import router as foothold_api_router
from foothold_sitac.foothold_router import router as foothold_router
from foothold_sitac.templater import env

config = get_config()

static_path = files("foothold_sitac") / "static"
app = FastAPI(title=config.web.title, version="0.1.0", description="Foothold Web Sitac")
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> str:
    template = env.get_template("home.html")
    return template.render(request=request)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse(url="/static/favicon.ico")


app.include_router(foothold_router, prefix="/foothold", include_in_schema=False)
app.include_router(foothold_api_router, prefix="/api/foothold", tags=["foothold"])
app.include_router(briefing_router, prefix="/foothold/briefing", include_in_schema=False)
app.include_router(briefing_api_router, prefix="/api/briefing", tags=["briefing"])
