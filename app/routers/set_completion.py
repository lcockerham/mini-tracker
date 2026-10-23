import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Mini

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()

# Catch-all for minis sold on their own, not a set anyone completes.
NOT_A_SET = "Individual"


def slot_key(mini_number: Optional[str], name: Optional[str]) -> str:
    """The figure a mini fills in its set, so variants of one figure share a slot.

    Variants share a base number: "10A"/"10B", and invisible versions like "46/6" (figure 46,
    a variant of #6). Unnumbered minis fall back to their name without parenthesized variant
    notes or "Invisible": "Goblin (mace)" and "Goblin (sword)" are one figure.
    """
    number = (mini_number or "").strip()
    if number:
        if "/" in number:
            number = number.split("/")[1].strip()
        match = re.fullmatch(r"(.*?\d+)[A-Za-z]?", number)
        base = match.group(1) if match else number
        return "#" + (str(int(base)) if base.isdigit() else base.lower())
    plain = re.sub(r"\(.*?\)|\binvisible\b", "", (name or "").lower())
    return "name:" + re.sub(r"[^a-z0-9]", "", plain)


def is_variant(name: Optional[str]) -> bool:
    """Invisible and alternate paint/sculpt versions are variants of a figure, not figures."""
    return bool(re.search(r"\binvisible\b|\balternate (paint|sculpt)\b", (name or "").lower()))


@dataclass
class SetProgress:
    set_name: str
    owned: int = 0
    total: int = 0
    # One entry per missing figure: every variant that would fill it.
    missing: list[list[Mini]] = field(default_factory=list)

    @property
    def percent(self) -> int:
        return round(100 * self.owned / self.total)


def set_progress(minis: list[Mini]) -> list[SetProgress]:
    slots: dict[str, dict[str, list[Mini]]] = {}
    for mini in minis:
        slots.setdefault(mini.set_name, {}).setdefault(
            slot_key(mini.mini_number, mini.name), []
        ).append(mini)

    progress = []
    for set_name, figures in slots.items():
        # A variant numbered on its own ("46 Drizzt (Invisible)") isn't needed to complete the set,
        # but owning one still fills its base figure's slot when they share a number.
        required = [
            variants
            for variants in figures.values()
            if not all(is_variant(m.name) for m in variants)
        ]
        if not required:
            continue
        entry = SetProgress(set_name=set_name, total=len(required))
        for variants in required:
            if any(m.quantity > 0 for m in variants):
                entry.owned += 1
            else:
                entry.missing.append(variants)
        progress.append(entry)
    return progress


@router.get("/minis/sets")
def set_completion(request: Request, db: Session = Depends(get_db)):
    minis = (
        db.query(Mini)
        .filter(
            Mini.set_name.isnot(None),
            Mini.set_name != "",
            Mini.set_name != NOT_A_SET,
            # Chase figures are bonus pulls; a set is complete without them.
            or_(Mini.rarity.is_(None), func.lower(Mini.rarity) != "chase"),
        )
        .order_by(Mini.id)
        .all()
    )
    progress = set_progress(minis)
    in_progress = sorted(
        (p for p in progress if 0 < p.owned < p.total),
        key=lambda p: (-p.owned / p.total, p.total - p.owned, p.set_name.lower()),
    )
    complete = sorted((p for p in progress if p.owned == p.total), key=lambda p: p.set_name.lower())
    return templates.TemplateResponse(
        request,
        "minis/sets.html",
        {
            "in_progress": in_progress,
            "complete": complete,
            "not_started_count": sum(1 for p in progress if p.owned == 0),
        },
    )
