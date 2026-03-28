
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db
from app.models import Paint

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/paints")
def list_paints(request: Request, db: Session = Depends(get_db)):
    paints = db.query(Paint).order_by(Paint.brand, Paint.name).all()
    return templates.TemplateResponse("paints/list.html", {
        "request": request,
        "paints": paints,
    })


@router.post("/paints")
def create_paint(
    brand: str = Form(...),
    name: str = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    paint = Paint(brand=brand, name=name, quantity=quantity)
    db.add(paint)
    db.commit()
    return RedirectResponse(url="/paints", status_code=303)


@router.post("/paints/{paint_id}/edit")
def update_paint(
    paint_id: int,
    brand: str = Form(...),
    name: str = Form(...),
    quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    paint = db.query(Paint).get(paint_id)
    paint.brand = brand
    paint.name = name
    paint.quantity = quantity
    db.commit()
    return RedirectResponse(url="/paints", status_code=303)
