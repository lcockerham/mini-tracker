import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from app.database import Base, list_migrations, upgrade_schema

OLD_DB_SQL = Path(__file__).parent / "fixtures" / "mini_tracker_2026-10-11.sql"


def make_engine(path):
    return create_engine(f"sqlite:///{path}")


def ledger(path):
    with sqlite3.connect(path) as conn:
        return [name for (name,) in conn.execute("SELECT filename FROM schema_migrations")]


def columns_by_table(engine):
    inspector = inspect(engine)
    return {
        table: {column["name"] for column in inspector.get_columns(table)}
        for table in inspector.get_table_names()
    }


def all_migration_names():
    return [migration.name for migration in list_migrations()]


@pytest.fixture()
def fresh_columns(tmp_path):
    engine = make_engine(tmp_path / "fresh.db")
    upgrade_schema(engine)
    return columns_by_table(engine)


def test_new_database_gets_current_schema_and_every_migration_recorded(tmp_path):
    path = tmp_path / "mini_tracker.db"
    engine = make_engine(path)

    upgrade_schema(engine)

    assert ledger(path) == all_migration_names()
    assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())
    assert not (tmp_path / "backups").exists()


def test_upgrade_from_older_database_copy(tmp_path, fresh_columns):
    path = tmp_path / "mini_tracker.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(OLD_DB_SQL.read_text())
    engine = make_engine(path)

    upgrade_schema(engine)

    assert ledger(path) == all_migration_names()
    # Same tables and columns as a database built from today's models.
    assert columns_by_table(engine) == fresh_columns
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT name, source_url FROM minis").fetchall() == [
            ("Owlbear", None)
        ]
        assert conn.execute("SELECT title, format_availability, setting FROM books").fetchall() == [
            ("Monster Manual", "both", None)
        ]
    # The pre-migration copy was kept.
    (backup,) = (tmp_path / "backups").glob("mini_tracker.*.db")
    with sqlite3.connect(backup) as conn:
        assert "source_url" not in {row[1] for row in conn.execute("PRAGMA table_info(minis)")}

    # A second startup has nothing to do.
    upgrade_schema(engine)
    assert ledger(path) == all_migration_names()
    assert len(list((tmp_path / "backups").glob("*.db"))) == 1


def test_database_patched_by_old_startup_code_is_recorded_without_changes(tmp_path):
    """A current database from before versioning already has every ADDED_COLUMNS column."""
    path = tmp_path / "mini_tracker.db"
    engine = make_engine(path)
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    upgrade_schema(engine)

    assert ledger(path) == all_migration_names()


def test_versioned_database_applies_only_pending_migrations(tmp_path, fresh_columns):
    path = tmp_path / "mini_tracker.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(OLD_DB_SQL.read_text())
    engine = make_engine(path)
    upgrade_schema(engine)
    # Roll the database back to version 2.
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE books DROP COLUMN setting")
        conn.execute("DELETE FROM schema_migrations WHERE filename LIKE '003_%'")

    upgrade_schema(engine)

    assert ledger(path) == all_migration_names()
    assert columns_by_table(engine) == fresh_columns


def test_failed_migration_is_rolled_back_and_not_recorded(tmp_path):
    migrations_dir = tmp_path / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_add_minis_base_size.sql").write_text(
        "ALTER TABLE minis ADD COLUMN base_size VARCHAR(20);\n"
    )
    (migrations_dir / "002_broken.sql").write_text(
        "ALTER TABLE minis ADD COLUMN sculptor VARCHAR(100);\nSELECT * FROM no_such_table;\n"
    )
    path = tmp_path / "mini_tracker.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE schema_migrations (filename VARCHAR(100) PRIMARY KEY)")
    engine = make_engine(path)

    with pytest.raises(RuntimeError, match="002_broken.sql failed and was rolled back"):
        upgrade_schema(engine, migrations_dir)

    assert ledger(path) == ["001_add_minis_base_size.sql"]
    minis_columns = columns_by_table(engine)["minis"]
    assert "base_size" in minis_columns
    assert "sculptor" not in minis_columns


def test_migration_files_are_numbered_without_gaps():
    numbers = [int(name[:3]) for name in all_migration_names()]
    assert numbers == list(range(1, len(numbers) + 1))
