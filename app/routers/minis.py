from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Mini, MiniStatus, Paint

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


def _filtered_minis_query(
    db: Session,
    search: Optional[str],
    creature_type: Optional[str],
    manufacturer: Optional[str],
    status: Optional[str],
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
    return query


def _navigation_query(
    search: Optional[str],
    creature_type: Optional[str],
    manufacturer: Optional[str],
    status: Optional[str],
) -> str:
    params = []
    for key, value in (
        ("search", search),
        ("creature_type", creature_type),
        ("manufacturer", manufacturer),
        ("status", status),
    ):
        if value:
            params.append((key, value))
    return urlencode(params)


def _navigation_query_from_request(request: Request) -> str:
    return _navigation_query(
        request.query_params.get("search"),
        request.query_params.get("creature_type"),
        request.query_params.get("manufacturer"),
        request.query_params.get("status"),
    )


@router.get("/minis")
def list_minis(
    request: Request,
    search: Optional[str] = None,
    creature_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _filtered_minis_query(db, search, creature_type, manufacturer, status).options(
        selectinload(Mini.photos)
    )

    minis = query.order_by(Mini.name, Mini.id).all()
    return templates.TemplateResponse(
        request,
        "minis/list.html",
        {
            "minis": minis,
            "search": search,
            "creature_type": creature_type,
            "manufacturer": manufacturer,
            "status": status,
            "navigation_query": _navigation_query(search, creature_type, manufacturer, status),
        },
    )


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
def get_mini(
    request: Request,
    mini_id: int,
    search: Optional[str] = None,
    creature_type: Optional[str] = None,
    manufacturer: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    mini = db.query(Mini).get(mini_id)
    navigation_minis = (
        _filtered_minis_query(db, search, creature_type, manufacturer, status)
        .order_by(Mini.name, Mini.id)
        .all()
    )
    current_index = next(
        (index for index, item in enumerate(navigation_minis) if item.id == mini_id),
        None,
    )
    previous_mini = None
    next_mini = None
    if current_index is not None:
        if current_index > 0:
            previous_mini = navigation_minis[current_index - 1]
        if current_index + 1 < len(navigation_minis):
            next_mini = navigation_minis[current_index + 1]

    navigation_query = _navigation_query(search, creature_type, manufacturer, status)
    all_paints = db.query(Paint).order_by(Paint.brand, Paint.name).all()
    return templates.TemplateResponse(
        request,
        "minis/detail.html",
        {
            "mini": mini,
            "all_paints": all_paints,
            "previous_mini": previous_mini,
            "next_mini": next_mini,
            "mini_position": current_index + 1 if current_index is not None else None,
            "mini_count": len(navigation_minis),
            "navigation_query": navigation_query,
            "minis_url": f"/minis?{navigation_query}" if navigation_query else "/minis",
        },
    )


@router.post("/minis/{mini_id}/edit")
def update_mini(
    request: Request,
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
    navigation_query = _navigation_query_from_request(request)
    mini_url = f"/minis/{mini_id}"
    if navigation_query:
        mini_url = f"{mini_url}?{navigation_query}"
    return RedirectResponse(url=mini_url, status_code=303)


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
