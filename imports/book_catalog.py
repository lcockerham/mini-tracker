import pandas as pd
from sqlalchemy.orm import Session

from app.models import Book, GameSystem

TRUE_VALUES = {"true", "1", "yes", "y", "x"}


def _parse_bool(val) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    return str(val).strip().lower() in TRUE_VALUES


def import_book_catalog(file_path: str, db: Session) -> dict:
    """Import a generic book catalog CSV as Books.

    Expected columns: title, game_system, category, publisher,
    owns_physical, owns_digital, notes. Unlike the DriveThruRPG importer,
    ownership is read from the CSV rather than assumed - a blank
    owns_physical/owns_digital means the book is catalogued but not
    marked as owned. Rows whose title+game_system already exist are
    skipped to avoid duplicates on repeat imports.
    """
    df = pd.read_csv(file_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "title" not in df.columns:
        raise ValueError(
            f"Could not find a title column. Found columns: {list(df.columns)}"
        )

    game_systems = {gs.name.lower(): gs for gs in db.query(GameSystem).all()}
    existing = {
        (title, gs_id)
        for title, gs_id in db.query(Book.title, Book.game_system_id).all()
    }

    added = 0
    skipped = 0

    for _, row in df.iterrows():
        def cell(col):
            val = row.get(col)
            if pd.isna(val):
                return None
            val = str(val).strip()
            return val or None

        title = cell("title")
        if not title:
            skipped += 1
            continue

        game_system_id = None
        game_system_name = cell("game_system")
        if game_system_name:
            gs = game_systems.get(game_system_name.lower())
            if gs is None:
                gs = GameSystem(name=game_system_name)
                db.add(gs)
                db.flush()
                game_systems[game_system_name.lower()] = gs
            game_system_id = gs.id

        if (title, game_system_id) in existing:
            skipped += 1
            continue

        book = Book(
            title=title,
            game_system_id=game_system_id,
            category=cell("category"),
            publisher=cell("publisher"),
            owns_physical=_parse_bool(row.get("owns_physical")),
            owns_digital=_parse_bool(row.get("owns_digital")),
            notes=cell("notes"),
        )
        db.add(book)
        existing.add((title, game_system_id))
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}
