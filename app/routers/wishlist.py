from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Mini, MiniStatus, WishlistItem

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/wishlist")
def list_wishlist(request: Request, db: Session = Depends(get_db)):
    items = db.query(WishlistItem).order_by(WishlistItem.name).all()
    return templates.TemplateResponse(request, "wishlist/list.html", {
        "items": items,
    })


@router.post("/wishlist")
def create_wishlist_item(
    name: str = Form(...),
    manufacturer: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    item = WishlistItem(
        name=name,
        manufacturer=manufacturer or None,
        notes=notes or None,
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/wishlist", status_code=303)


@router.post("/wishlist/{item_id}/purchase")
def purchase_wishlist_item(
    item_id: int,
    quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    item = db.query(WishlistItem).get(item_id)
    mini = Mini(
        name=item.name,
        manufacturer=item.manufacturer,
        status=MiniStatus.UNPAINTED,
        quantity=quantity,
    )
    db.add(mini)
    db.delete(item)
    db.commit()
    return RedirectResponse(url=f"/minis/{mini.id}", status_code=303)


@router.post("/wishlist/{item_id}/delete")
def delete_wishlist_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    item = db.query(WishlistItem).get(item_id)
    db.delete(item)
    db.commit()
    return RedirectResponse(url="/wishlist", status_code=303)
