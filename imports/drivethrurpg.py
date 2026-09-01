import pandas as pd
from sqlalchemy.orm import Session

from app.models import Book

# DriveThruRPG's order history / library export column names aren't
# officially documented, so this maps the common variants seen in their
# CSV exports. Verify against your actual export and extend as needed.
COLUMN_MAP = {
    "title": "title",
    "product title": "title",
    "product name": "title",
    "item": "title",
    "publisher": "publisher",
    "publisher name": "publisher",
    "order date": "acquired_date",
    "purchase date": "acquired_date",
    "date": "acquired_date",
    "product url": "drivethrurpg_url",
    "url": "drivethrurpg_url",
    "link": "drivethrurpg_url",
}


def import_drivethrurpg_csv(file_path: str, db: Session) -> dict:
    """Import a DriveThruRPG order history / library CSV export as Books.

    Every imported row is marked owns_digital=True. Rows whose title
    already exists in the Book table are skipped to avoid duplicates on
    repeat imports.
    """
    df = pd.read_csv(file_path)
    df.columns = [str(c).strip().lower() for c in df.columns]

    mapped = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[col]

    if "title" not in mapped.values():
        raise ValueError(
            f"Could not find a title column. Found columns: {list(df.columns)}"
        )

    existing_titles = {title for (title,) in db.query(Book.title).all()}

    added = 0
    skipped = 0

    for _, row in df.iterrows():
        data = {}
        for orig_col, model_field in mapped.items():
            val = row.get(orig_col)
            if pd.isna(val):
                val = None
            else:
                val = str(val).strip() if val is not None else None
            data[model_field] = val

        title = data.get("title")
        if not title or title in existing_titles:
            skipped += 1
            continue

        acquired_date = None
        if data.get("acquired_date"):
            try:
                acquired_date = pd.to_datetime(data["acquired_date"]).date()
            except (ValueError, TypeError):
                acquired_date = None

        book = Book(
            title=title,
            publisher=data.get("publisher"),
            drivethrurpg_url=data.get("drivethrurpg_url"),
            acquired_date=acquired_date,
            owns_digital=True,
        )
        db.add(book)
        existing_titles.add(title)
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}
