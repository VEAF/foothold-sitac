from importlib.resources import files

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from foothold_sitac.config import get_config
from foothold_sitac.foothold_api_router import router as foothold_api_router
from foothold_sitac.foothold_router import router as foothold_router
from foothold_sitac.i18n import LANGUAGE_COOKIE, LANGUAGES, LanguageMiddleware, safe_next_path
from foothold_sitac.templater import env

config = get_config()

static_path = files("foothold_sitac") / "static"
app = FastAPI(title=config.web.title, version="0.1.0", description="Foothold Web Sitac")
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
app.add_middleware(LanguageMiddleware)

LANGUAGE_COOKIE_MAX_AGE = 365 * 24 * 3600


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> str:
    template = env.get_template("home.html")
    return template.render(request=request)


@app.get("/lang/{language}", include_in_schema=False)
async def set_language(language: str, next: str | None = None) -> RedirectResponse:
    """The language selector: remember the chosen language in a cookie and go back to the page."""
    if language not in LANGUAGES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown language '{language}'")
    response = RedirectResponse(url=safe_next_path(next), status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(LANGUAGE_COOKIE, language, max_age=LANGUAGE_COOKIE_MAX_AGE, samesite="lax")
    return response


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse(url="/static/favicon.ico")


app.include_router(foothold_router, prefix="/foothold", include_in_schema=False)
app.include_router(foothold_api_router, prefix="/api/foothold", tags=["foothold"])
