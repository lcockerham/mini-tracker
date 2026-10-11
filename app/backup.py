import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

KEEP_BACKUPS = 3


def backup_database(db: Session) -> Optional[Path]:
    """Copy the SQLite file to backups/ before a bulk write, keeping only the newest few."""
    database = db.get_bind().url.database
    if not database or database == ":memory:":
        return None
    source = Path(database).resolve()
    backups = source.parent / "backups"
    backups.mkdir(exist_ok=True)
    target = backups / f"{source.stem}.{datetime.now():%Y%m%d%H%M%S}.db"
    shutil.copy2(source, target)
    for old in sorted(backups.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)[
        KEEP_BACKUPS:
    ]:
        old.unlink()
    return target
