from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine


def _migrate_leads_columns() -> None:
    """Add Phase 4 columns to existing SQLite databases."""
    inspector = inspect(engine)
    if "leads" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("leads")}
    migrations = [
        ("pipeline_status", "VARCHAR(32) NOT NULL DEFAULT 'pending'"),
        ("pipeline_error", "TEXT"),
        ("pipeline_step_id", "VARCHAR(64)"),
        ("processing_time_ms", "INTEGER"),
    ]

    with engine.begin() as conn:
        for column, definition in migrations:
            if column not in existing:
                conn.execute(text(f"ALTER TABLE leads ADD COLUMN {column} {definition}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_leads_columns()
