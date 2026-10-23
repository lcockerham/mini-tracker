"""Fill in Dwarven Forge store links and pictures for sets and pieces.

dwarven_forge_links.tsv was built from dwarvenforge.com's public product catalog (its Shopify
products.json, loaded in a browser because the site rate-limits scripts). Columns, no header:

    kind (S = set, P = piece), SKU or piece code, how it matched, product handle, image URL

"how" is "sku" when the store lists that exact SKU (pieces sell as IN-<code>-U/P), "skuVariant:<sku>"
when only another paint scheme of the same sculpt is sold (CV-609 matched CV-609-I, the ice version),
or "image" when only a picture filename carries the code. A set matched by picture alone gets the
picture but no link, because the page it was found on sells a bigger bundle.

Only empty fields are filled, so anything set by hand in the app is kept.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import DwarvenForgePiece, DwarvenForgeSet

LINKS_TSV = Path(__file__).with_name("dwarven_forge_links.tsv")
PRODUCT_URL = "https://www.dwarvenforge.com/products/{handle}"


@dataclass
class LinkResult:
    links_added: int = 0
    images_added: int = 0
    unknown_keys: int = 0


def apply_links(db: Session, rows: list[list[str]]) -> LinkResult:
    sets = {s.sku: s for s in db.query(DwarvenForgeSet)}
    pieces = {p.code: p for p in db.query(DwarvenForgePiece)}
    result = LinkResult()
    for kind, key, how, handle, image_url in rows:
        target = (sets if kind == "S" else pieces).get(key)
        if target is None:
            result.unknown_keys += 1
            continue
        if not target.source_url and not (kind == "S" and how == "image"):
            target.source_url = PRODUCT_URL.format(handle=handle)
            result.links_added += 1
        if not target.image_url:
            target.image_url = image_url
            result.images_added += 1
    db.commit()
    return result


def main() -> int:
    from app.backup import backup_database
    from app.database import SessionLocal, upgrade_schema

    with LINKS_TSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))

    upgrade_schema()
    db = SessionLocal()
    try:
        backup = backup_database(db)
        result = apply_links(db, rows)
    finally:
        db.close()

    print(f"Dwarven Forge links from {LINKS_TSV.name} ({len(rows)} matches)")
    print(f"  backup: {backup}")
    print(f"  links added: {result.links_added}, pictures added: {result.images_added}")
    if result.unknown_keys:
        print(f"  not in the collection, skipped: {result.unknown_keys}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
