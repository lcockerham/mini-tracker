from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Mini, MiniStatus

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    total = db.query(func.sum(Mini.quantity)).scalar() or 0

    # Status breakdown
    status_counts = {}
    for status in MiniStatus:
        count = (
            db.query(func.sum(Mini.quantity))
            .filter(Mini.status == status)
            .scalar() or 0
        )
        status_counts[status.value] = count

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

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total": total,
        "status_counts": status_counts,
        "manufacturers": manufacturers,
        "timeline": timeline,
    })
