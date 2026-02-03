from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Photo

router = APIRouter()


@router.post("/minis/{mini_id}/photos")
def add_photo(
    mini_id: int,
    url: str = Form(...),
    db: Session = Depends(get_db),
):
    photo = Photo(mini_id=mini_id, url=url)
    db.add(photo)
    db.commit()
    return RedirectResponse(url=f"/minis/{mini_id}", status_code=303)


@router.post("/minis/{mini_id}/photos/{photo_id}/delete")
def delete_photo(
    mini_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
):
    photo = db.query(Photo).get(photo_id)
    if photo and photo.mini_id == mini_id:
        db.delete(photo)
        db.commit()
    return RedirectResponse(url=f"/minis/{mini_id}", status_code=303)
