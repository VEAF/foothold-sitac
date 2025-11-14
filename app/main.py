import uvicorn
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Request
from app.foothold_router import router as foothold_router
from app.templater import env

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    template = env.get_template("home.html")
    return template.render(request=request)

app.include_router(foothold_router, prefix="/foothold")

if __name__ == "__main__":

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True
    )
