from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import Base, engine
from app.routers import dashboard, minis, paints, photos, wishlist

app = FastAPI(title="Mini-Tracker", description="RPG miniature collection tracker")
app.include_router(minis.router)
app.include_router(paints.router)
app.include_router(wishlist.router)
app.include_router(photos.router)
app.include_router(dashboard.router)

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


@app.get("/import")
def import_form(request: Request):
    return templates.TemplateResponse("import.html", {"request": request})


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
            return templates.TemplateResponse("import.html", {
                "request": request,
                "result": result,
            })
        finally:
            db.close()
    except Exception as e:
        return templates.TemplateResponse("import.html", {
            "request": request,
            "error": str(e),
        })
