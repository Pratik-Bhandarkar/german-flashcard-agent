# db.py
# Manages the database connection and session lifecycle.
# All database operations go through the session provided here.
# This is the single place where the database connection is configured.

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base
from pipeline.config import DATABASE_PATH


# The engine is the core connection to the database.
# We use the SQLite file path from config.
# The check_same_thread=False is required for SQLite when used with FastAPI
# because FastAPI handles requests in multiple threads.
engine = create_engine(
    f"sqlite:///{DATABASE_PATH}",
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory that creates new database sessions.
# Each request to the API will get its own session.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db() -> None:
    """
    Creates all tables in the database if they don't exist yet.
    Call this once when the application starts.
    """
    Base.metadata.create_all(bind=engine)


def migrate_db() -> None:
    """Add columns that did not exist in earlier versions of the schema."""
    with engine.connect() as conn:
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(flashcards)"))
        }
        if "seeded_from" not in existing:
            conn.execute(text("ALTER TABLE flashcards ADD COLUMN seeded_from TEXT"))
            conn.commit()
        if "last_reviewed" not in existing:
            conn.execute(text("ALTER TABLE flashcards ADD COLUMN last_reviewed TEXT"))
            conn.commit()


def get_db():
    """
    Provides a database session for a single request.
    Automatically closes the session when the request is done.
    This is used as a FastAPI dependency in the route handlers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()