from itertools import groupby
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import DwarvenForgePiece, DwarvenForgeSet, DwarvenForgeSetPiece

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()

NO_TERRAIN_LINE = "Other"


def image_at_width(url: Optional[str], width: int) -> Optional[str]:
    """Ask Shopify's CDN for a resized copy; its originals are ~2000px, too heavy for thumbnails."""
    if url and url.startswith("https://cdn.shopify.com/"):
        return f"{url}{'&' if '?' in url else '?'}width={width}"
    return url


templates.env.filters["at_width"] = image_at_width


def _get_or_create_piece(db: Session, code: str) -> DwarvenForgePiece:
    piece = db.query(DwarvenForgePiece).filter(DwarvenForgePiece.code == code).first()
    if piece is None:
        piece = DwarvenForgePiece(code=code)
        db.add(piece)
    return piece


@router.get("/dwarven-forge")
def list_sets(request: Request, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DwarvenForgeSet).options(selectinload(DwarvenForgeSet.contents))
    if search:
        query = query.filter(
            or_(DwarvenForgeSet.name.ilike(f"%{search}%"), DwarvenForgeSet.sku.ilike(f"%{search}%"))
        )
    sets = sorted(
        query.all(),
        key=lambda s: ((s.terrain_line or NO_TERRAIN_LINE).lower(), s.name.lower()),
    )
    lines = [
        (line, list(items))
        for line, items in groupby(sets, key=lambda s: s.terrain_line or NO_TERRAIN_LINE)
    ]
    return templates.TemplateResponse(
        request,
        "dwarven_forge/sets.html",
        {
            "lines": lines,
            "search": search,
            "set_count": len(sets),
            "piece_total": sum(s.piece_total for s in sets),
        },
    )


@router.get("/dwarven-forge/sets/new")
def create_set_form(request: Request):
    return templates.TemplateResponse(request, "dwarven_forge/set_create.html", {})


@router.post("/dwarven-forge/sets/new")
def create_set(
    sku: str = Form(...),
    name: str = Form(...),
    terrain_line: Optional[str] = Form(None),
    paint_type: Optional[str] = Form(None),
    copies: int = Form(1),
    db: Session = Depends(get_db),
):
    df_set = DwarvenForgeSet(
        sku=sku.strip(),
        name=name,
        terrain_line=terrain_line or None,
        paint_type=paint_type or None,
        copies=copies,
    )
    db.add(df_set)
    db.commit()
    return RedirectResponse(url=f"/dwarven-forge/sets/{df_set.id}", status_code=303)


@router.get("/dwarven-forge/sets/{set_id}")
def get_set(request: Request, set_id: int, db: Session = Depends(get_db)):
    df_set = db.query(DwarvenForgeSet).get(set_id)
    contents = sorted(df_set.contents, key=lambda entry: entry.piece.code)
    return templates.TemplateResponse(
        request, "dwarven_forge/set_detail.html", {"set": df_set, "contents": contents}
    )


@router.post("/dwarven-forge/sets/{set_id}/edit")
def update_set(
    set_id: int,
    sku: str = Form(...),
    name: str = Form(...),
    terrain_line: Optional[str] = Form(None),
    paint_type: Optional[str] = Form(None),
    copies: int = Form(1),
    source_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    df_set = db.query(DwarvenForgeSet).get(set_id)
    df_set.sku = sku.strip()
    df_set.name = name
    df_set.terrain_line = terrain_line or None
    df_set.paint_type = paint_type or None
    df_set.copies = copies
    df_set.source_url = source_url or None
    df_set.image_url = image_url or None
    df_set.notes = notes or None
    db.commit()
    return RedirectResponse(url=f"/dwarven-forge/sets/{set_id}", status_code=303)


@router.post("/dwarven-forge/sets/{set_id}/pieces")
def add_piece_to_set(
    set_id: int,
    code: str = Form(...),
    count: int = Form(1),
    db: Session = Depends(get_db),
):
    df_set = db.query(DwarvenForgeSet).get(set_id)
    piece = _get_or_create_piece(db, code.strip())
    entry = next((e for e in df_set.contents if e.piece is piece), None)
    if entry:
        entry.count = count
    else:
        df_set.contents.append(DwarvenForgeSetPiece(piece=piece, count=count))
    db.commit()
    return RedirectResponse(url=f"/dwarven-forge/sets/{set_id}", status_code=303)


@router.post("/dwarven-forge/sets/{set_id}/pieces/{piece_id}/remove")
def remove_piece_from_set(set_id: int, piece_id: int, db: Session = Depends(get_db)):
    entry = db.query(DwarvenForgeSetPiece).get((set_id, piece_id))
    if entry:
        db.delete(entry)
        db.commit()
    return RedirectResponse(url=f"/dwarven-forge/sets/{set_id}", status_code=303)


@router.post("/dwarven-forge/sets/{set_id}/delete")
def delete_set(set_id: int, db: Session = Depends(get_db)):
    db.delete(db.query(DwarvenForgeSet).get(set_id))
    db.commit()
    return RedirectResponse(url="/dwarven-forge", status_code=303)


@router.get("/dwarven-forge/pieces")
def list_pieces(request: Request, search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DwarvenForgePiece).options(
        selectinload(DwarvenForgePiece.set_entries).selectinload(DwarvenForgeSetPiece.set)
    )
    if search:
        query = query.filter(
            or_(
                DwarvenForgePiece.code.ilike(f"%{search}%"),
                DwarvenForgePiece.name.ilike(f"%{search}%"),
            )
        )
    pieces = query.order_by(func.lower(DwarvenForgePiece.code)).all()
    return templates.TemplateResponse(
        request,
        "dwarven_forge/pieces.html",
        {
            "pieces": pieces,
            "search": search,
            "owned_total": sum(p.owned_total for p in pieces),
        },
    )


@router.get("/dwarven-forge/pieces/new")
def create_piece_form(request: Request):
    return templates.TemplateResponse(request, "dwarven_forge/piece_create.html", {})


@router.post("/dwarven-forge/pieces/new")
def create_piece(
    code: str = Form(...),
    name: Optional[str] = Form(None),
    loose_quantity: int = Form(1),
    db: Session = Depends(get_db),
):
    piece = _get_or_create_piece(db, code.strip())
    if name:
        piece.name = name
    piece.loose_quantity = (piece.loose_quantity or 0) + loose_quantity
    db.commit()
    return RedirectResponse(url=f"/dwarven-forge/pieces/{piece.id}", status_code=303)


@router.get("/dwarven-forge/pieces/{piece_id}")
def get_piece(request: Request, piece_id: int, db: Session = Depends(get_db)):
    piece = db.query(DwarvenForgePiece).get(piece_id)
    entries = sorted(piece.set_entries, key=lambda entry: entry.set.name.lower())
    return templates.TemplateResponse(
        request, "dwarven_forge/piece_detail.html", {"piece": piece, "entries": entries}
    )


@router.post("/dwarven-forge/pieces/{piece_id}/edit")
def update_piece(
    piece_id: int,
    code: str = Form(...),
    name: Optional[str] = Form(None),
    loose_quantity: int = Form(0),
    source_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    piece = db.query(DwarvenForgePiece).get(piece_id)
    piece.code = code.strip()
    piece.name = name or None
    piece.loose_quantity = loose_quantity
    piece.source_url = source_url or None
    piece.image_url = image_url or None
    piece.notes = notes or None
    db.commit()
    return RedirectResponse(url=f"/dwarven-forge/pieces/{piece_id}", status_code=303)


@router.post("/dwarven-forge/pieces/{piece_id}/delete")
def delete_piece(piece_id: int, db: Session = Depends(get_db)):
    db.delete(db.query(DwarvenForgePiece).get(piece_id))
    db.commit()
    return RedirectResponse(url="/dwarven-forge/pieces", status_code=303)
