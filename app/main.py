from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.database import engine, Base
from app.routers import minis

app = FastAPI(title="Mini-Tracker", description="RPG miniature collection tracker")
app.include_router(minis.router)

app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=app_dir / "static"), name="static")
templates = Jinja2Templates(directory=app_dir / "templates")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def index():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/minis")
