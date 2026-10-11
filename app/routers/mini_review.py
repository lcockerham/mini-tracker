import re
from itertools import groupby
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.backup import backup_database
from app.database import get_db
from app.models import Mini, MiniCandidate, MiniStatus, Photo

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()


def _base_name_key(value: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", value or "").lower())


def _approve(db: Session, candidate: MiniCandidate) -> None:
    mini = Mini(
        name=candidate.name,
        manufacturer="Wizkids",
        set_name=candidate.set_name,
        mini_number=candidate.mini_number,
        size=candidate.size,
        rarity=candidate.rarity,
        status=MiniStatus.PRE_PAINTED,
        quantity=0,
    )
    if candidate.image_url:
        mini.photos.append(Photo(url=candidate.image_url))
    db.add(mini)
    db.flush()
    candidate.status = "approved"
    candidate.mini_id = mini.id


def _redirect(message: str) -> RedirectResponse:
    return RedirectResponse(url=f"/minis/review?{urlencode({'message': message})}", status_code=303)


@router.get("/minis/review")
def review_candidates(
    request: Request, message: Optional[str] = None, db: Session = Depends(get_db)
):
    candidates = (
        db.query(MiniCandidate)
        .filter(MiniCandidate.status == "pending")
        .order_by(MiniCandidate.set_name, MiniCandidate.id)
        .all()
    )
    # The sync only checks within the matching set; flag same-named minis elsewhere so a renamed
    # set (e.g. "Red Ghost Dragon" vs "Adult Red Ghost Dragon") doesn't become a duplicate.
    minis_by_name: dict[str, list[Mini]] = {}
    if candidates:
        for mini in db.query(Mini).filter(Mini.manufacturer == "Wizkids"):
            minis_by_name.setdefault(_base_name_key(mini.name), []).append(mini)
    possible_matches = {
        candidate.id: minis_by_name.get(_base_name_key(candidate.name), [])[:3]
        for candidate in candidates
    }
    groups = [(name, list(items)) for name, items in groupby(candidates, key=lambda c: c.set_name)]
    return templates.TemplateResponse(
        request,
        "minis/review.html",
        {
            "groups": groups,
            "pending_count": len(candidates),
            "possible_matches": possible_matches,
            "message": message,
        },
    )


@router.post("/minis/review/set")
def review_set(set_name: str = Form(...), action: str = Form(...), db: Session = Depends(get_db)):
    candidates = (
        db.query(MiniCandidate)
        .filter(MiniCandidate.status == "pending", MiniCandidate.set_name == set_name)
        .all()
    )
    if action == "approve":
        if len(candidates) > 1:
            backup_database(db)
        for candidate in candidates:
            _approve(db, candidate)
    else:
        for candidate in candidates:
            candidate.status = "rejected"
    db.commit()
    verb = "Added" if action == "approve" else "Rejected"
    return _redirect(f"{verb} {len(candidates)} from {set_name}")


@router.post("/minis/review/{candidate_id}/approve")
def approve_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(MiniCandidate, candidate_id)
    if candidate and candidate.status == "pending":
        _approve(db, candidate)
        db.commit()
        return _redirect(f"Added {candidate.name}")
    return _redirect("Nothing to add")


@router.post("/minis/review/{candidate_id}/reject")
def reject_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(MiniCandidate, candidate_id)
    if candidate and candidate.status == "pending":
        candidate.status = "rejected"
        db.commit()
        return _redirect(f"Rejected {candidate.name}")
    return _redirect("Nothing to reject")
