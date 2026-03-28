from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Mini, MiniStatus, Paint

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/minis")
def list_minis(
    request: Request,
    search: Optional[str] = None,
    creature_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Mini)
    if search:
        query = query.filter(Mini.name.ilike(f"%{search}%"))
    if creature_type:
        query = query.filter(Mini.creature_type.ilike(f"%{creature_type}%"))
    if manufacturer:
        query = query.filter(Mini.manufacturer.ilike(f"%{manufacturer}%"))
    if status:
        query = query.filter(Mini.status == MiniStatus(status))

    minis = query.order_by(Mini.name).all()
    return templates.TemplateResponse(request, "minis/list.html", {
        "minis": minis,
        "search": search,
        "creature_type": creature_type,
        "manufacturer": manufacturer,
        "status": status,
    })


@router.get("/minis/new")
def create_mini_form(request: Request):
    return templates.TemplateResponse(request, "minis/create.html", {})


@router.post("/minis/new")
def create_mini(
    name: str = Form(...),
    creature_type: Optional[str] = Form(None),
    manufacturer: Optional[str] = Form(None),
    product_line: Optional[str] = Form(None),
    set_name: Optional[str] = Form(None),
    mini_number: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    status: str = Form("Unpainted"),
    quantity: int = Form(1),
    completion_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    mini = Mini(
        name=name,
        creature_type=creature_type or None,
        manufacturer=manufacturer or None,
        product_line=product_line or None,
        set_name=set_name or None,
        mini_number=mini_number or None,
        size=size or None,
        status=MiniStatus(status),
        quantity=quantity,
        completion_date=date.fromisoformat(completion_date) if completion_date else None,
        notes=notes or None,
    )
    db.add(mini)
    db.commit()
    return RedirectResponse(url=f"/minis/{mini.id}", status_code=303)


@router.get("/minis/{mini_id}")
def get_mini(request: Request, mini_id: int, db: Session = Depends(get_db)):
    mini = db.query(Mini).get(mini_id)
    all_paints = db.query(Paint).order_by(Paint.brand, Paint.name).all()
    return templates.TemplateResponse(request, "minis/detail.html", {
        "mini": mini,
        "all_paints": all_paints,
    })


@router.post("/minis/{mini_id}/edit")
def update_mini(
    mini_id: int,
    name: str = Form(...),
    creature_type: Optional[str] = Form(None),
    manufacturer: Optional[str] = Form(None),
    product_line: Optional[str] = Form(None),
    set_name: Optional[str] = Form(None),
    mini_number: Optional[str] = Form(None),
    size: Optional[str] = Form(None),
    status: str = Form("Unpainted"),
    quantity: int = Form(1),
    completion_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    mini = db.query(Mini).get(mini_id)
    mini.name = name
    mini.creature_type = creature_type or None
    mini.manufacturer = manufacturer or None
    mini.product_line = product_line or None
    mini.set_name = set_name or None
    mini.mini_number = mini_number or None
    mini.size = size or None
    mini.status = MiniStatus(status)
    mini.quantity = quantity
    mini.completion_date = date.fromisoformat(completion_date) if completion_date else None
    mini.notes = notes or None
    db.commit()
    return RedirectResponse(url=f"/minis/{mini_id}", status_code=303)


@router.post("/minis/{mini_id}/paints")
def add_paint_to_mini(
    mini_id: int,
    paint_id: int = Form(...),
    db: Session = Depends(get_db),
):
    mini = db.query(Mini).get(mini_id)
    paint = db.query(Paint).get(paint_id)
    if paint and paint not in mini.paints:
        mini.paints.append(paint)
        db.commit()
    return RedirectResponse(url=f"/minis/{mini_id}", status_code=303)


@router.post("/minis/{mini_id}/paints/{paint_id}/remove")
def remove_paint_from_mini(
    mini_id: int,
    paint_id: int,
    db: Session = Depends(get_db),
):
    mini = db.query(Mini).get(mini_id)
    paint = db.query(Paint).get(paint_id)
    if paint and paint in mini.paints:
        mini.paints.remove(paint)
        db.commit()
    return RedirectResponse(url=f"/minis/{mini_id}", status_code=303)
