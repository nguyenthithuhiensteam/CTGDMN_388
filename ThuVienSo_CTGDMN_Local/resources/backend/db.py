from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
)
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.dialects import postgresql, sqlite

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "ct388_local.db"


def now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DATABASE_PATH}"
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, future=True)
    return _engine


def is_sqlite() -> bool:
    return get_engine().dialect.name == "sqlite"


metadata = MetaData()


def ts_default_col(name: str) -> Column:
    return Column(name, String, default=now_str)


age_groups = Table(
    "age_groups",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("sort_order", Integer, default=0),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

domains = Table(
    "domains",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("sort_order", Integer, default=0),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

competencies = Table(
    "competencies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    Column("domain_id", Integer, ForeignKey("domains.id")),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

qualities = Table(
    "qualities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True),
    Column("name", String, nullable=False),
    Column("description", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

yccd = Table(
    "yccd",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True, nullable=False),
    Column("content", Text, nullable=False),
    Column("age_group_id", Integer, ForeignKey("age_groups.id")),
    Column("domain_id", Integer, ForeignKey("domains.id")),
    Column("competency_id", Integer, ForeignKey("competencies.id")),
    Column("quality_id", Integer, ForeignKey("qualities.id")),
    Column("source_note", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

milestones = Table(
    "milestones",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("age_group_id", Integer, ForeignKey("age_groups.id")),
    Column("domain_id", Integer, ForeignKey("domains.id")),
    Column("title", String, nullable=False),
    Column("description", Text),
    Column("evidence_hint", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

activities = Table(
    "activities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String, unique=True),
    Column("title", String, nullable=False),
    Column("age_group_id", Integer, ForeignKey("age_groups.id")),
    Column("domain_id", Integer, ForeignKey("domains.id")),
    Column("yccd_id", Integer, ForeignKey("yccd.id")),
    Column("objective", Text),
    Column("materials", Text),
    Column("steps", Text),
    Column("notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

rubrics = Table(
    "rubrics",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("yccd_id", Integer, ForeignKey("yccd.id")),
    Column("title", String, nullable=False),
    Column("criteria", Text),
    Column("evidence_hint", Text),
    Column("support_next", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

year_plans = Table(
    "year_plans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_year", String, nullable=False),
    Column("age_group_id", Integer, ForeignKey("age_groups.id")),
    Column("title", String),
    Column("notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

month_plans = Table(
    "month_plans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("year_plan_id", Integer, ForeignKey("year_plans.id")),
    Column("month_number", Integer),
    Column("theme_context", Text),
    Column("notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

week_plans = Table(
    "week_plans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("month_plan_id", Integer, ForeignKey("month_plans.id")),
    Column("week_number", Integer),
    Column("title", String),
    Column("notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

day_plans = Table(
    "day_plans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("week_plan_id", Integer, ForeignKey("week_plans.id")),
    Column("plan_date", String),
    Column("title", String),
    Column("care_nurture_notes", Text),
    Column("education_notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

# ─── Multi-tenant: schools & user accounts ─────────────────────────────────
schools = Table(
    "schools",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("city", String),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False),
    Column("email", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("full_name", String),
    Column("role", String, nullable=False),  # 'admin' | 'teacher'
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

# ─── Per-school operational data ───────────────────────────────────────────
children = Table(
    "children",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False),
    Column("child_code", String),
    Column("full_name", String, nullable=False),
    Column("date_of_birth", String),
    Column("gender", String),
    Column("class_name", String),
    Column("age_group_id", Integer, ForeignKey("age_groups.id")),
    Column("notes", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

observations = Table(
    "observations",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False),
    Column("child_id", Integer, ForeignKey("children.id")),
    Column("observed_at", String),
    Column("context", Text),
    Column("note", Text, nullable=False),
    Column("evidence", Text),
    Column("support_next", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

assessments = Table(
    "assessments",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False),
    Column("child_id", Integer, ForeignKey("children.id")),
    Column("yccd_id", Integer, ForeignKey("yccd.id")),
    Column("assessment_date", String),
    Column("evidence", Text),
    Column("progress_note", Text),
    Column("support_next", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

portfolio = Table(
    "portfolio",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False),
    Column("child_id", Integer, ForeignKey("children.id")),
    Column("title", String, nullable=False),
    Column("artifact_type", String),
    Column("artifact_path", String),
    Column("note", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

school_settings = Table(
    "school_settings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("school_id", Integer, ForeignKey("schools.id"), nullable=False, unique=True),
    Column("school_name", String),
    Column("school_year", String),
    Column("city", String),
    Column("principal_name", String),
    Column("contact_info", String),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)

# Legacy desktop machine-lock license table (kept for the offline single-machine app).
licenses = Table(
    "licenses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("license_key", String),
    Column("machine_code", String),
    Column("status", String, default="not_configured"),
    Column("note", Text),
    ts_default_col("created_at"),
    ts_default_col("updated_at"),
)


def init_database() -> None:
    metadata.create_all(get_engine())


def get_connection() -> Connection:
    """Return a live SQLAlchemy connection. Caller is responsible for closing it
    (use as a context manager: `with get_connection() as conn:`)."""
    return get_engine().connect()


def rows_as_dicts(result: Iterable[Any]) -> list[dict[str, Any]]:
    return [dict(r._mapping) for r in result]


def row_as_dict(row: Any) -> dict[str, Any] | None:
    return dict(row._mapping) if row is not None else None


def fetch_table_counts(table_names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with get_connection() as conn:
        for table_name in table_names:
            result = conn.exec_driver_sql(f'SELECT COUNT(*) AS total FROM "{table_name}"')
            row = result.fetchone()
            counts[table_name] = int(row[0] if row else 0)
    return counts


def upsert_returning_id(
    conn: Connection,
    table: Table,
    values: dict[str, Any],
    conflict_cols: list[str],
    update_cols: list[str] | None = None,
    coalesce_cols: list[str] | None = None,
) -> int:
    """Insert `values` into `table`; on conflict of `conflict_cols`, update `update_cols`
    (defaults to all non-conflict, non-id columns present in `values`) by overwriting with
    the new value. Columns listed in `coalesce_cols` are instead set to
    COALESCE(new_value, existing_value) — i.e. keep the old value when the new one is None.
    Returns the row id."""
    if "updated_at" in table.c and "updated_at" not in values:
        values = {**values, "updated_at": now_str()}
    coalesce_cols = coalesce_cols or []
    update_cols = update_cols if update_cols is not None else [
        c for c in values if c not in conflict_cols and c != "id"
    ]
    dialect_insert = postgresql.insert if get_engine().dialect.name == "postgresql" else sqlite.insert
    stmt = dialect_insert(table).values(**values)
    if update_cols:
        set_ = {}
        for col in update_cols:
            if col in coalesce_cols:
                set_[col] = func.coalesce(getattr(stmt.excluded, col), table.c[col])
            else:
                set_[col] = getattr(stmt.excluded, col)
        stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=set_)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=conflict_cols)
    stmt = stmt.returning(table.c.id)
    result = conn.execute(stmt)
    row = result.fetchone()
    if row is not None:
        return int(row[0])
    # on_conflict_do_nothing with no update_cols and an existing row returns no row.
    lookup = {c: values[c] for c in conflict_cols}
    existing = conn.execute(table.select().filter_by(**lookup)).fetchone()
    return int(existing[0])


def insert_returning_id(conn: Connection, table: Table, values: dict[str, Any]) -> int:
    stmt = table.insert().values(**values).returning(table.c.id)
    result = conn.execute(stmt)
    return int(result.fetchone()[0])
