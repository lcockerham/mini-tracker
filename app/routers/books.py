from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, GameSystem

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()
BOOK_COVER_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "books"
BOOK_COVER_EXTENSIONS = (".webp", ".jpg", ".jpeg", ".png")


def _book_cover_url(book_id: int) -> Optional[str]:
    for extension in BOOK_COVER_EXTENSIONS:
        if (BOOK_COVER_DIR / f"{book_id}{extension}").is_file():
            return f"/static/images/books/{book_id}{extension}"
    return None


def _filtered_books_query(
    db: Session,
    search: Optional[str],
    game_system_id: Optional[int],
    ownership: Optional[str],
):
    query = db.query(Book)
    if search:
        query = query.filter(Book.title.ilike(f"%{search}%"))
    if game_system_id:
        query = query.filter(Book.game_system_id == game_system_id)
    if ownership == "physical":
        query = query.filter(Book.owns_physical.is_(True))
    elif ownership == "digital":
        query = query.filter(Book.owns_digital.is_(True))
    return query


def _navigation_query(
    search: Optional[str],
    game_system_id: Optional[int | str],
    ownership: Optional[str],
) -> str:
    params = []
    if search:
        params.append(("search", search))
    if game_system_id:
        params.append(("game_system_id", str(game_system_id)))
    if ownership in ("physical", "digital"):
        params.append(("ownership", ownership))
    return urlencode(params)


def _navigation_query_from_request(request: Request) -> str:
    return _navigation_query(
        request.query_params.get("search"),
        request.query_params.get("game_system_id"),
        request.query_params.get("ownership"),
    )


@router.get("/books")
def list_books(
    request: Request,
    search: Optional[str] = None,
    game_system_id: Optional[str] = None,
    ownership: Optional[str] = None,
    db: Session = Depends(get_db),
):
    game_system_id_int = int(game_system_id) if game_system_id else None

    query = _filtered_books_query(db, search, game_system_id_int, ownership)
    books = query.order_by(Book.title, Book.id).all()
    game_systems = db.query(GameSystem).order_by(GameSystem.name).all()
    return templates.TemplateResponse(request, "books/list.html", {
        "books": books,
        "game_systems": game_systems,
        "search": search,
        "game_system_id": game_system_id_int,
        "ownership": ownership,
        "navigation_query": _navigation_query(
            search, game_system_id_int, ownership
        ),
    })


@router.get("/books/new")
def create_book_form(request: Request, db: Session = Depends(get_db)):
    game_systems = db.query(GameSystem).order_by(GameSystem.name).all()
    return templates.TemplateResponse(request, "books/create.html", {
        "game_systems": game_systems,
    })


@router.post("/books/new")
def create_book(
    title: str = Form(...),
    game_system_id: Optional[str] = Form(None),
    publisher: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    owns_physical: Optional[str] = Form(None),
    owns_digital: Optional[str] = Form(None),
    physical_location: Optional[str] = Form(None),
    pdf_url: Optional[str] = Form(None),
    drivethrurpg_url: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    acquired_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    book = Book(
        title=title,
        game_system_id=int(game_system_id) if game_system_id else None,
        publisher=publisher or None,
        category=category or None,
        owns_physical=bool(owns_physical),
        owns_digital=bool(owns_digital),
        physical_location=physical_location or None,
        pdf_url=pdf_url or None,
        drivethrurpg_url=drivethrurpg_url or None,
        isbn=isbn or None,
        acquired_date=date.fromisoformat(acquired_date) if acquired_date else None,
        notes=notes or None,
    )
    db.add(book)
    db.commit()
    return RedirectResponse(url=f"/books/{book.id}", status_code=303)


@router.get("/books/import")
def import_books_form(request: Request):
    return templates.TemplateResponse(request, "books/import.html", {})


@router.post("/books/import")
async def import_books(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    import tempfile

    from imports.drivethrurpg import import_drivethrurpg_csv

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = import_drivethrurpg_csv(tmp_path, db)
        return templates.TemplateResponse(request, "books/import.html", {
            "result": result,
        })
    except Exception as e:
        return templates.TemplateResponse(request, "books/import.html", {
            "error": str(e),
        })


@router.get("/books/import-catalog")
def import_book_catalog_form(request: Request):
    return templates.TemplateResponse(request, "books/import_catalog.html", {})


@router.post("/books/import-catalog")
async def import_book_catalog_route(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    import tempfile

    from imports.book_catalog import import_book_catalog

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = import_book_catalog(tmp_path, db)
        return templates.TemplateResponse(request, "books/import_catalog.html", {
            "result": result,
        })
    except Exception as e:
        return templates.TemplateResponse(request, "books/import_catalog.html", {
            "error": str(e),
        })


@router.get("/books/{book_id}")
def get_book(
    request: Request,
    book_id: int,
    search: Optional[str] = None,
    game_system_id: Optional[str] = None,
    ownership: Optional[str] = None,
    db: Session = Depends(get_db),
):
    book = db.query(Book).get(book_id)
    game_system_id_int = int(game_system_id) if game_system_id else None
    navigation_books = (
        _filtered_books_query(db, search, game_system_id_int, ownership)
        .order_by(Book.title, Book.id)
        .all()
    )
    current_index = next(
        (index for index, item in enumerate(navigation_books) if item.id == book_id),
        None,
    )
    previous_book = None
    next_book = None
    if current_index is not None:
        if current_index > 0:
            previous_book = navigation_books[current_index - 1]
        if current_index + 1 < len(navigation_books):
            next_book = navigation_books[current_index + 1]

    navigation_query = _navigation_query(search, game_system_id_int, ownership)
    game_systems = db.query(GameSystem).order_by(GameSystem.name).all()
    return templates.TemplateResponse(request, "books/detail.html", {
        "book": book,
        "game_systems": game_systems,
        "cover_image_url": _book_cover_url(book_id),
        "previous_book": previous_book,
        "next_book": next_book,
        "book_position": current_index + 1 if current_index is not None else None,
        "book_count": len(navigation_books),
        "navigation_query": navigation_query,
        "books_url": f"/books?{navigation_query}" if navigation_query else "/books",
    })


@router.post("/books/{book_id}/edit")
def update_book(
    request: Request,
    book_id: int,
    title: str = Form(...),
    game_system_id: Optional[str] = Form(None),
    publisher: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    owns_physical: Optional[str] = Form(None),
    owns_digital: Optional[str] = Form(None),
    physical_location: Optional[str] = Form(None),
    pdf_url: Optional[str] = Form(None),
    drivethrurpg_url: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    acquired_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    book = db.query(Book).get(book_id)
    book.title = title
    book.game_system_id = int(game_system_id) if game_system_id else None
    book.publisher = publisher or None
    book.category = category or None
    book.owns_physical = bool(owns_physical)
    book.owns_digital = bool(owns_digital)
    book.physical_location = physical_location or None
    book.pdf_url = pdf_url or None
    book.drivethrurpg_url = drivethrurpg_url or None
    book.isbn = isbn or None
    book.acquired_date = date.fromisoformat(acquired_date) if acquired_date else None
    book.notes = notes or None
    db.commit()
    navigation_query = _navigation_query_from_request(request)
    book_url = f"/books/{book_id}"
    if navigation_query:
        book_url = f"{book_url}?{navigation_query}"
    return RedirectResponse(url=book_url, status_code=303)


@router.post("/books/{book_id}/delete")
def delete_book(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).get(book_id)
    db.delete(book)
    db.commit()
    navigation_query = _navigation_query_from_request(request)
    books_url = f"/books?{navigation_query}" if navigation_query else "/books"
    return RedirectResponse(url=books_url, status_code=303)
