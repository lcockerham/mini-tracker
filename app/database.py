import logging
import re
import sqlite3
from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.backup import backup_file

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///mini_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATION_NAME = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")

# These were the old ADDED_COLUMNS startup patch, which ran without recording anything, so a
# database from before versioned migrations may already have their column.
PRE_VERSIONING_MIGRATIONS = {
    "001_add_books_format_availability.sql",
    "002_add_minis_source_url.sql",
    "003_add_books_setting.sql",
}


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def list_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    migrations = sorted(migrations_dir.glob("*.sql"))
    for migration in migrations:
        if not MIGRATION_NAME.match(migration.name):
            raise ValueError(f"Migration file {migration.name} isn't named like 004_add_thing.sql")
    return migrations


def upgrade_schema(bind: Engine = engine, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    """Create missing tables, then apply the numbered SQL files in app/migrations/ in order.

    Each applied file is recorded in the schema_migrations table, so its highest-numbered row
    is the database's schema version. A brand-new database gets the current schema from the
    models and is recorded as having every migration. Before applying anything to an existing
    database it's copied to backups/.
    """
    import app.models  # noqa: F401  (register tables on Base)

    migrations = list_migrations(migrations_dir)
    existing_tables = set(inspect(bind).get_table_names())
    pre_versioning = bool(existing_tables) and "schema_migrations" not in existing_tables
    applied: set[str] = set()
    if "schema_migrations" in existing_tables:
        with bind.connect() as conn:
            applied = set(conn.execute(text("SELECT filename FROM schema_migrations")).scalars())
    pending = [m for m in migrations if m.name not in applied]

    backup = None
    if existing_tables and pending:
        backup = backup_file(bind.url.database)
        logger.info("Backed up the database to %s before migrating.", backup)

    # create_all() only adds missing tables; it never changes an existing one.
    Base.metadata.create_all(bind=bind)
    with bind.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                " filename VARCHAR(100) PRIMARY KEY,"
                " applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
        )
        if not existing_tables:
            for migration in migrations:
                conn.execute(
                    text("INSERT INTO schema_migrations (filename) VALUES (:filename)"),
                    {"filename": migration.name},
                )
            logger.info("Created a new database at schema version %s.", len(migrations))
            return

    raw = bind.raw_connection()
    try:
        db = raw.driver_connection
        for migration in pending:
            # One transaction per file, so a failed migration leaves no partial change or record.
            # The filename is safe to inline: list_migrations() checked it against MIGRATION_NAME.
            script = (
                f"BEGIN;\n{migration.read_text()}\n"
                f"INSERT INTO schema_migrations (filename) VALUES ('{migration.name}');\nCOMMIT;"
            )
            try:
                db.executescript(script)
            except sqlite3.OperationalError as error:
                db.rollback()
                if (
                    pre_versioning
                    and migration.name in PRE_VERSIONING_MIGRATIONS
                    and str(error).startswith("duplicate column name")
                ):
                    db.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (?)", (migration.name,)
                    )
                    db.commit()
                    logger.info("Recorded %s; the old startup patch applied it.", migration.name)
                    continue
                raise RuntimeError(
                    f"Migration {migration.name} failed and was rolled back ({error}). "
                    f"The database before migrating was backed up to {backup}."
                ) from error
            logger.info("Applied migration %s.", migration.name)
    finally:
        raw.close()
