from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine


def _migrate_table_columns(table: str, migrations: list[tuple[str, str]]) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    with engine.begin() as conn:
        for column, definition in migrations:
            if column not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def _migrate_leads_columns() -> None:
    _migrate_table_columns(
        "leads",
        [
            ("pipeline_status", "VARCHAR(32) NOT NULL DEFAULT 'pending'"),
            ("pipeline_error", "TEXT"),
            ("pipeline_step_id", "VARCHAR(64)"),
            ("processing_time_ms", "INTEGER"),
            ("state_snapshot", "JSON"),
            ("human_review_status", "VARCHAR(32)"),
            ("human_review_notes", "TEXT"),
        ],
    )


def _migrate_agent_runs_columns() -> None:
    _migrate_table_columns(
        "agent_runs",
        [
            ("prompt_version", "VARCHAR(32)"),
            ("tools_used", "JSON"),
            ("retrieved_documents", "JSON"),
            ("confidence", "FLOAT"),
            ("latency_ms", "INTEGER"),
            ("token_usage", "INTEGER"),
        ],
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_leads_columns()
    _migrate_agent_runs_columns()
