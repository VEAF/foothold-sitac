import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from foothold_sitac.config import get_config
from foothold_sitac.foothold_api_router import router as foothold_api_router
from foothold_sitac.foothold_router import router as foothold_router
from foothold_sitac.templater import env
from foothold_sitac.unit_names import UNIT_NAMES_PATH, get_unit_display_names, refresh_unit_display_names

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    """Ensure the foothold_sitac logger is visible alongside uvicorn output."""
    root = logging.getLogger("foothold_sitac")
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
        root.addHandler(handler)
    root.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None]:
    """Startup / shutdown lifecycle hook."""
    _configure_logging()
    config = get_config()
    dcs_install = config.dcs.install_path

    if dcs_install and Path(dcs_install).exists():
        logger.info("DCS install path configured: %s", dcs_install)
        count = refresh_unit_display_names(Path(dcs_install))
        if count:
            logger.info("Refreshed %d unit display names at startup", count)
            get_unit_display_names.cache_clear()
        else:
            logger.warning("No unit mappings extracted from %s", dcs_install)
    elif dcs_install:
        logger.warning("DCS install path configured but does not exist: %s", dcs_install)
    else:
        logger.info("Répertoire DCS non configuré (dcs.install_path)")
        if UNIT_NAMES_PATH.exists():
            names = get_unit_display_names()
            logger.info("Using existing unit display names file (%d entries)", len(names))
        else:
            logger.info("No unit display names available — unit codes will be shown as-is")

    yield


config = get_config()

static_path = files("foothold_sitac") / "static"
app = FastAPI(title=config.web.title, version="0.1.0", description="Foothold Web Sitac", lifespan=lifespan)
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
