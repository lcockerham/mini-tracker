from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///mini_tracker.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# create_all() does not add columns to an existing SQLite database.
ADDED_COLUMNS = [
    ("books", "format_availability", "VARCHAR(20)"),
    ("minis", "source_url", "VARCHAR(500)"),
]


def upgrade_schema():
    import app.models  # noqa: F401  (register tables on Base)

    Base.metadata.create_all(bind=engine)
    for table, column, column_type in ADDED_COLUMNS:
        if column not in {c["name"] for c in inspect(engine).get_columns(table)}:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"))
