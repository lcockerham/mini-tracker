"""Import a Dwarven Forge inventory CSV into the df_sets / df_pieces tables.

The CSV has one row per piece per set: Code, Name, Count, Set Name (the terrain line), SKU,
Bundle Name, Paint Type. A set owned more than once repeats its whole block of rows, so the
number of repeats is the number of copies.

Re-running only adds sets and pieces that aren't in the database yet; it never overwrites
anything edited in the app.
"""

import argparse
import csv
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import DwarvenForgePiece, DwarvenForgeSet, DwarvenForgeSetPiece

DEFAULT_CSV = Path.home() / "Developer" / "mini-data" / "Dwarven Forge - Sheet1.csv"


@dataclass
class SetRows:
    sku: str
    name: str
    terrain_line: Optional[str]
    paint_type: Optional[str]
    copies: int = 1
    # piece code -> count in one copy of the set
    pieces: dict[str, int] = field(default_factory=dict)


@dataclass
class ImportResult:
    sets_added: int = 0
    sets_skipped: int = 0
    pieces_added: int = 0


def _blank_to_none(value: str) -> Optional[str]:
    value = value.strip()
    return None if value in ("", "N/A") else value


def parse_rows(rows: list[dict[str, str]]) -> tuple[list[SetRows], dict[str, Optional[str]]]:
    """Group CSV rows into sets and collect each piece code's name."""
    sets: dict[str, SetRows] = {}
    occurrences: dict[str, Counter] = {}
    piece_names: dict[str, Optional[str]] = {}
    for row in rows:
        sku = row["SKU"].strip()
        code = row["Code"].strip()
        entry = sets.setdefault(
            sku,
            SetRows(
                sku=sku,
                name=row["Bundle Name"].strip() or sku,
                terrain_line=_blank_to_none(row["Set Name"]),
                paint_type=_blank_to_none(row["Paint Type"]),
            ),
        )
        entry.pieces[code] = int(row["Count"])
        occurrences.setdefault(sku, Counter())[code] += 1
        # Keep the first name seen; a code's name varies only in wording between sets.
        if not piece_names.get(code):
            piece_names[code] = _blank_to_none(row["Name"])

    for sku, counts in occurrences.items():
        repeats = set(counts.values())
        if len(repeats) != 1:
            raise ValueError(f"{sku}: pieces repeat unevenly {dict(counts)}; can't tell copies")
        sets[sku].copies = repeats.pop()
    return list(sets.values()), piece_names


def import_collection(db: Session, rows: list[dict[str, str]]) -> ImportResult:
    set_rows, piece_names = parse_rows(rows)
    result = ImportResult()

    pieces = {piece.code: piece for piece in db.query(DwarvenForgePiece)}
    for code, name in piece_names.items():
        if code not in pieces:
            pieces[code] = DwarvenForgePiece(code=code, name=name)
            db.add(pieces[code])
            result.pieces_added += 1

    existing_skus = {sku for (sku,) in db.query(DwarvenForgeSet.sku)}
    for entry in set_rows:
        if entry.sku in existing_skus:
            result.sets_skipped += 1
            continue
        df_set = DwarvenForgeSet(
            sku=entry.sku,
            name=entry.name,
            terrain_line=entry.terrain_line,
            paint_type=entry.paint_type,
            copies=entry.copies,
        )
        df_set.contents = [
            DwarvenForgeSetPiece(piece=pieces[code], count=count)
            for code, count in entry.pieces.items()
        ]
        db.add(df_set)
        result.sets_added += 1
    db.commit()
    return result


def main() -> int:
    from app.backup import backup_database
    from app.database import SessionLocal, upgrade_schema

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv_path", nargs="?", type=Path, default=DEFAULT_CSV)
    args = parser.parse_args()

    with args.csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    upgrade_schema()
    db = SessionLocal()
    try:
        backup = backup_database(db)
        result = import_collection(db, rows)
    finally:
        db.close()

    print(f"Dwarven Forge import from {args.csv_path}")
    print(f"  backup: {backup}")
    print(f"  sets added: {result.sets_added}, already present: {result.sets_skipped}")
    print(f"  pieces added: {result.pieces_added}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
