from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Map

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()
MAP_IMAGE_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "maps"
MAP_IMAGE_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png")


def _map_image_url(map_id: int) -> Optional[str]:
    for extension in MAP_IMAGE_EXTENSIONS:
        if (MAP_IMAGE_DIR / f"{map_id}{extension}").is_file():
            return f"/static/images/maps/{map_id}{extension}"
    return None


@router.get("/maps")
def list_maps(
    request: Request,
    search: Optional[str] = None,
    ownership: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Map)
    if search:
        query = query.filter(Map.name.ilike(f"%{search}%"))
    if ownership == "physical":
        query = query.filter(Map.owns_physical.is_(True))
    elif ownership == "digital":
        query = query.filter(Map.owns_digital.is_(True))
    maps = query.order_by(Map.name, Map.id).all()
    return templates.TemplateResponse(request, "maps/list.html", {
        "maps": maps,
        "search": search,
        "ownership": ownership,
    })


@router.get("/maps/new")
def create_map_form(request: Request):
    return templates.TemplateResponse(request, "maps/create.html", {})


@router.post("/maps/new")
def create_map(
    name: str = Form(...),
    source: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    owns_physical: Optional[str] = Form(None),
    owns_digital: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    map_ = Map(
        name=name,
        source=source or None,
        size=size or None,
        owns_physical=bool(owns_physical),
        owns_digital=bool(owns_digital),
    )
    db.add(map_)
    db.commit()
    return RedirectResponse(url=f"/maps/{map_.id}", status_code=303)


@router.get("/maps/{map_id}")
def get_map(request: Request, map_id: int, db: Session = Depends(get_db)):
    map_ = db.query(Map).get(map_id)
    return templates.TemplateResponse(request, "maps/detail.html", {
        "map": map_,
        "image_url": _map_image_url(map_id),
    })


@router.post("/maps/{map_id}/edit")
def update_map(
    map_id: int,
    name: str = Form(...),
    source: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    owns_physical: Optional[str] = Form(None),
    owns_digital: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    map_ = db.query(Map).get(map_id)
    map_.name = name
    map_.source = source or None
    map_.size = size or None
    map_.owns_physical = bool(owns_physical)
    map_.owns_digital = bool(owns_digital)
    db.commit()
    return RedirectResponse(url=f"/maps/{map_id}", status_code=303)


@router.post("/maps/{map_id}/delete")
def delete_map(map_id: int, db: Session = Depends(get_db)):
    map_ = db.query(Map).get(map_id)
    db.delete(map_)
    db.commit()
    return RedirectResponse(url="/maps", status_code=303)
