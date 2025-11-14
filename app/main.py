import uvicorn
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from app.config import get_config
from app.foothold_router import router as foothold_router
from app.templater import env

config = get_config()

app = FastAPI(
    title=config.web.title,
    version="0.1.0",
    description="Foothold Web Sitac"
)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    template = env.get_template("home.html")
    return template.render(request=request)

app.include_router(foothold_router, prefix="/foothold", tags=["foothold"])

if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host=config.web.host,
        port=config.web.port,
        reload=config.web.reload,
    )
