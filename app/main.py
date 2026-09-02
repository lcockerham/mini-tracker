from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, SessionLocal, engine
from app.image_service import MEDIA_ROOT, ensure_media_directories
from app.models import GameSystem
from app.routers import books, dashboard, minis, paints, photos, wishlist

app = FastAPI(title="Mini-Tracker", description="RPG miniature collection tracker")
app.include_router(minis.router)
app.include_router(paints.router)
app.include_router(wishlist.router)
app.include_router(photos.router)
app.include_router(dashboard.router)
app.include_router(books.router)

DEFAULT_GAME_SYSTEMS = [
    "D&D 5e",
    "Pathfinder 2e",
    "Call of Cthulhu",
    "Savage Worlds",
    "System-agnostic",
    "Other",
]

app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=app_dir / "static"), name="static")
ensure_media_directories()
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
templates = Jinja2Templates(directory=app_dir / "templates")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = {name for (name,) in db.query(GameSystem.name).all()}
        for name in DEFAULT_GAME_SYSTEMS:
            if name not in existing:
                db.add(GameSystem(name=name))
        db.commit()
    finally:
        db.close()


@app.get("/")
def index():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/minis")


@app.get("/import")
def import_form(request: Request):
    return templates.TemplateResponse(request, "import.html", {})


@app.post("/import")
async def import_spreadsheet_route(request: Request, file: UploadFile = File(...)):
    import tempfile

    from app.database import SessionLocal
    from imports.spreadsheet import import_spreadsheet

    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        db = SessionLocal()
        try:
            result = import_spreadsheet(tmp_path, db)
            return templates.TemplateResponse(request, "import.html", {
                "result": result,
            })
        finally:
            db.close()
    except Exception as e:
        return templates.TemplateResponse(request, "import.html", {
            "error": str(e),
        })
