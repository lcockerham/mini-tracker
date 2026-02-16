import pandas as pd
from sqlalchemy.orm import Session

from app.models import Mini, MiniStatus

# Expected column mappings (case-insensitive, flexible matching)
COLUMN_MAP = {
    "name": "name",
    "mini name": "name",
    "miniature": "name",
    "creature_type": "creature_type",
    "creature type": "creature_type",
    "type": "creature_type",
    "manufacturer": "manufacturer",
    "brand": "manufacturer",
    "product_line": "product_line",
    "product line": "product_line",
    "line": "product_line",
    "set_name": "set_name",
    "set name": "set_name",
    "set": "set_name",
    "mini_number": "mini_number",
    "mini number": "mini_number",
    "number": "mini_number",
    "#": "mini_number",
    "sku": "mini_number",
    "size": "size",
    "status": "status",
    "quantity": "quantity",
    "qty": "quantity",
    "count": "quantity",
    "notes": "notes",
    "completion_date": "completion_date",
    "completion date": "completion_date",
    "date completed": "completion_date",
    "rarity": "rarity",
}

STATUS_MAP = {
    "unpainted": MiniStatus.UNPAINTED,
    "in progress": MiniStatus.IN_PROGRESS,
    "wip": MiniStatus.IN_PROGRESS,
    "done": MiniStatus.DONE,
    "painted": MiniStatus.DONE,
    "complete": MiniStatus.DONE,
    "completed": MiniStatus.DONE,
    "pre-painted": MiniStatus.PRE_PAINTED,
    "prepainted": MiniStatus.PRE_PAINTED,
    "pre painted": MiniStatus.PRE_PAINTED,
}

SIZE_MAP = {
    "tiny": "Tiny",
    "small": "Small",
    "medium": "Medium",
    "large": "Large",
    "huge": "Huge",
    "gargantuan": "Gargantuan",
    "humongous": "Gargantuan",
    "colossal": "Gargantuan",
}


def import_spreadsheet(file_path: str, db: Session) -> dict:
    """Import minis from an Excel spreadsheet. Returns stats dict."""
    df = pd.read_excel(file_path)

    # Normalize column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map columns to model fields
    mapped = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            mapped[col] = COLUMN_MAP[col]

    if "name" not in mapped.values():
        raise ValueError(
            f"Could not find a 'name' column. "
            f"Found columns: {list(df.columns)}"
        )

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

        name = data.get("name")
        if not name:
            skipped += 1
            continue

        # Parse status
        status = MiniStatus.UNPAINTED
        if data.get("status"):
            status_key = data["status"].lower()
            status = STATUS_MAP.get(status_key, MiniStatus.UNPAINTED)

        # Parse quantity
        quantity = 1
        if data.get("quantity"):
            try:
                quantity = int(float(data["quantity"]))
            except (ValueError, TypeError):
                quantity = 1

        # Parse completion date
        completion_date = None
        if data.get("completion_date"):
            try:
                parsed = pd.to_datetime(data["completion_date"])
                completion_date = parsed.date()
            except (ValueError, TypeError):
                completion_date = None

        # Normalize size
        size = None
        if data.get("size"):
            size = SIZE_MAP.get(data["size"].lower(), data["size"])

        mini = Mini(
            name=name,
            creature_type=data.get("creature_type"),
            manufacturer=data.get("manufacturer"),
            product_line=data.get("product_line"),
            set_name=data.get("set_name"),
            mini_number=data.get("mini_number"),
            size=size,
            rarity=data.get("rarity"),
            status=status,
            quantity=quantity,
            completion_date=completion_date,
            notes=data.get("notes"),
        )
        db.add(mini)
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}
