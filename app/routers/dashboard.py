from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, GameSystem, Mini, MiniStatus

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()

DND_EDITION_ORDER = [
    "OD&D",
    "D&D Basic",
    "D&D Expert",
    "AD&D 1e",
    "AD&D 2e",
    "D&D 3e",
    "D&D 4e",
    "D&D 5e",
]


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    total = db.query(func.sum(Mini.quantity)).scalar() or 0

    # Painting breakdown (excludes pre-painted)
    painting_statuses = [MiniStatus.UNPAINTED, MiniStatus.IN_PROGRESS, MiniStatus.DONE]
    status_counts = {}
    for status in painting_statuses:
        count = (
            db.query(func.sum(Mini.quantity))
            .filter(Mini.status == status)
            .scalar() or 0
        )
        label = "Painted" if status == MiniStatus.DONE else status.value
        status_counts[label] = count

    # Manufacturer breakdown
    manufacturer_rows = (
        db.query(Mini.manufacturer, func.sum(Mini.quantity))
        .group_by(Mini.manufacturer)
        .order_by(func.sum(Mini.quantity).desc())
        .all()
    )
    manufacturers = {
        (name or "Unknown"): count
        for name, count in manufacturer_rows
    }

    # Painting timeline (minis completed per month)
    timeline_rows = (
        db.query(
            func.strftime("%Y-%m", Mini.completion_date),
            func.count(Mini.id),
        )
        .filter(Mini.completion_date.isnot(None))
        .group_by(func.strftime("%Y-%m", Mini.completion_date))
        .order_by(func.strftime("%Y-%m", Mini.completion_date))
        .all()
    )
    timeline = {month: count for month, count in timeline_rows}

    # Book collection summary
    book_counts = {
        "Physical": db.query(Book).filter(Book.owns_physical.is_(True)).count(),
        "Digital": db.query(Book).filter(Book.owns_digital.is_(True)).count(),
    }
    total_books = db.query(Book).count()

    book_system_rows = (
        db.query(
            GameSystem.id,
            GameSystem.name,
            func.count(Book.id),
            func.sum(case((Book.owns_physical.is_(True), 1), else_=0)),
        )
        .select_from(Book)
        .outerjoin(GameSystem, Book.game_system_id == GameSystem.id)
        .group_by(GameSystem.name)
        .order_by(func.count(Book.id).desc())
        .all()
    )
    book_collection = []
    for system_id, name, total_count, physical_count in book_system_rows:
        edition = name or "Unassigned"
        if edition not in DND_EDITION_ORDER:
            continue
        physical_count = physical_count or 0
        book_collection.append({
            "system_id": system_id,
            "name": edition,
            "total": total_count,
            "physical": physical_count,
            "physical_percent": round(physical_count / total_count * 100, 1),
        })
    book_collection.sort(key=lambda item: DND_EDITION_ORDER.index(item["name"]))

    return templates.TemplateResponse(request, "dashboard.html", {
        "total": total,
        "status_counts": status_counts,
        "manufacturers": manufacturers,
        "timeline": timeline,
        "total_books": total_books,
        "book_counts": book_counts,
        "book_collection": book_collection,
    })
