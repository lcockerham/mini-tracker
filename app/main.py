import logging
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal, upgrade_schema
from app.models import GameSystem
from app.routers import books, dashboard, maps, mini_review, minis, paints, photos, wishlist

logger = logging.getLogger(__name__)

app = FastAPI(title="Mini-Tracker", description="RPG miniature collection tracker")
# Before minis so /minis/review isn't captured by /minis/{mini_id}.
app.include_router(mini_review.router)
app.include_router(minis.router)
app.include_router(paints.router)
app.include_router(wishlist.router)
app.include_router(photos.router)
app.include_router(dashboard.router)
app.include_router(books.router)
app.include_router(maps.router)

DEFAULT_GAME_SYSTEMS = [
    "D&D Basic",
    "D&D Expert",
    "D&D 5e",
    "Pathfinder 2e",
    "Call of Cthulhu",
    "Savage Worlds",
    "System-agnostic",
    "Other",
]

# Workbook uploads larger than this are rejected rather than copied to disk and parsed.
MAX_IMPORT_BYTES = 10 * 1024 * 1024
IMPORT_CHUNK_BYTES = 1024 * 1024

app_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=app_dir / "static"), name="static")
templates = Jinja2Templates(directory=app_dir / "templates")


@app.on_event("startup")
def on_startup():
    upgrade_schema()
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

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp_path = tmp.name
            size = 0
            while chunk := await file.read(IMPORT_CHUNK_BYTES):
                size += len(chunk)
                if size > MAX_IMPORT_BYTES:
                    return templates.TemplateResponse(request, "import.html", {
                        "error": (
                            f"File is too large. The limit is "
                            f"{MAX_IMPORT_BYTES // (1024 * 1024)} MB."
                        ),
                    }, status_code=413)
                tmp.write(chunk)

        db = SessionLocal()
        try:
            result = import_spreadsheet(tmp_path, db)
            return templates.TemplateResponse(request, "import.html", {
                "result": result,
            })
        finally:
            db.close()
    except Exception:
        logger.exception("Spreadsheet import failed for %r", file.filename)
        return templates.TemplateResponse(request, "import.html", {
            "error": (
                "Could not import that file. Make sure it is an Excel workbook (.xlsx) "
                "with a 'name' column."
            ),
        })
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
