from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.image_service import (
    MAX_UPLOAD_BYTES,
    ImageValidationError,
    attach_uploaded_image,
    delete_book_with_images,
    remove_book_image,
    set_primary_image,
)
from app.models import Book, BookImage, GameSystem

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter()
BOOKS_PER_PAGE = 50


def _get_book_or_404(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


def _detail_context(db: Session, book: Book, **extra):
    context = {
        "book": book,
        "game_systems": db.query(GameSystem).order_by(GameSystem.name).all(),
    }
    context.update(extra)
    return context


@router.get("/books")
def list_books(
    request: Request,
    search: Optional[str] = None,
    game_system_id: Optional[str] = None,
    ownership: Optional[str] = None,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    game_system_id_int = int(game_system_id) if game_system_id else None

    query = db.query(Book)
    if search:
        query = query.filter(Book.title.ilike(f"%{search}%"))
    if game_system_id_int:
        query = query.filter(Book.game_system_id == game_system_id_int)
    if ownership == "physical":
        query = query.filter(Book.owns_physical.is_(True))
    elif ownership == "digital":
        query = query.filter(Book.owns_digital.is_(True))

    total_books = query.count()
    total_pages = max(1, (total_books + BOOKS_PER_PAGE - 1) // BOOKS_PER_PAGE)
    page = min(page, total_pages)
    books = (
        query.options(
            selectinload(Book.image_links).selectinload(BookImage.image_asset)
        )
        .order_by(Book.title)
        .offset((page - 1) * BOOKS_PER_PAGE)
        .limit(BOOKS_PER_PAGE)
        .all()
    )
    game_systems = db.query(GameSystem).order_by(GameSystem.name).all()
    return templates.TemplateResponse(request, "books/list.html", {
        "books": books,
        "game_systems": game_systems,
        "search": search,
        "game_system_id": game_system_id_int,
        "ownership": ownership,
        "page": page,
        "total_pages": total_pages,
        "total_books": total_books,
        "page_start": (page - 1) * BOOKS_PER_PAGE + 1 if total_books else 0,
        "page_end": min(page * BOOKS_PER_PAGE, total_books),
        "previous_url": str(request.url.include_query_params(page=page - 1)),
        "next_url": str(request.url.include_query_params(page=page + 1)),
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
def get_book(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    return templates.TemplateResponse(
        request,
        "books/detail.html",
        _detail_context(db, book),
    )


@router.post("/books/{book_id}/edit")
def update_book(
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
    book = _get_book_or_404(db, book_id)
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
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/delete")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = _get_book_or_404(db, book_id)
    delete_book_with_images(db, book)
    return RedirectResponse(url="/books", status_code=303)


@router.post("/books/{book_id}/images")
async def upload_book_image(
    request: Request,
    book_id: int,
    image: UploadFile = File(...),
    make_primary: Optional[str] = Form(None),
    creator: Optional[str] = Form(None),
    attribution_text: Optional[str] = Form(None),
    license_name: Optional[str] = Form(None),
    license_url: Optional[str] = Form(None),
    source_page_url: Optional[str] = Form(None),
    rights_status: str = Form("user_owned"),
    db: Session = Depends(get_db),
):
    book = _get_book_or_404(db, book_id)
    if rights_status not in {"user_owned", "licensed", "unknown"}:
        raise HTTPException(status_code=400, detail="Invalid rights status")

    contents = await image.read(MAX_UPLOAD_BYTES + 1)
    try:
        attach_uploaded_image(
            db,
            book,
            contents,
            image.content_type,
            make_primary=bool(make_primary) or not book.image_links,
            creator=creator,
            attribution_text=attribution_text,
            license_name=license_name,
            license_url=license_url,
            source_page_url=source_page_url,
            rights_status=rights_status,
        )
    except ImageValidationError as exc:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "books/detail.html",
            _detail_context(db, book, image_error=str(exc)),
            status_code=400,
        )
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/images/{image_asset_id}/primary")
def make_book_image_primary(
    book_id: int,
    image_asset_id: int,
    db: Session = Depends(get_db),
):
    book = _get_book_or_404(db, book_id)
    link = db.get(BookImage, (book_id, image_asset_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Book image not found")
    set_primary_image(db, book, link)
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)


@router.post("/books/{book_id}/images/{image_asset_id}/remove")
def remove_image_from_book(
    book_id: int,
    image_asset_id: int,
    db: Session = Depends(get_db),
):
    book = _get_book_or_404(db, book_id)
    link = db.get(BookImage, (book_id, image_asset_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Book image not found")
    remove_book_image(db, book, link)
    return RedirectResponse(url=f"/books/{book_id}", status_code=303)
