from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from backend import db
from backend.init_db import TABLES

router = APIRouter(tags=["curriculum"])


def age_filter(age_group: str | None) -> tuple[str, dict[str, Any]]:
    if not age_group:
        return "", {}
    return (
        " AND age_group_id IN (SELECT id FROM age_groups WHERE code=:age_code OR name LIKE :age_like)",
        {"age_code": age_group, "age_like": f"%{age_group}%"},
    )


@router.get("/api/health")
def health() -> dict[str, Any]:
    try:
        with db.get_connection() as conn:
            conn.exec_driver_sql("SELECT 1")
        connected = True
    except Exception:
        connected = False
    return {
        "status": "ok",
        "app": "CT388 App",
        "database_dialect": db.get_engine().dialect.name,
        "database_connected": connected,
    }


@router.get("/api/stats")
def stats() -> dict[str, object]:
    counts = db.fetch_table_counts(TABLES)
    return {"status": "ok", "tables": counts, "total_records": sum(counts.values())}


@router.get("/api/age-groups")
def age_groups() -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(text("SELECT * FROM age_groups ORDER BY sort_order, code, name"))
        return db.rows_as_dicts(result)


@router.get("/api/domains")
def domains() -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(text("SELECT * FROM domains ORDER BY sort_order, code, name"))
        return db.rows_as_dicts(result)


@router.get("/api/competencies")
def competencies(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        if age_group:
            result = conn.execute(
                text(
                    """
                    SELECT DISTINCT c.*, d.name AS domain_name
                    FROM competencies c
                    LEFT JOIN domains d ON d.id = c.domain_id
                    JOIN yccd y ON y.competency_id = c.id
                    JOIN age_groups ag ON ag.id = y.age_group_id
                    WHERE ag.code = :age_code OR ag.name LIKE :age_like
                    ORDER BY c.code, c.name
                    """
                ),
                {"age_code": age_group, "age_like": f"%{age_group}%"},
            )
        else:
            result = conn.execute(
                text(
                    """
                    SELECT c.*, d.name AS domain_name
                    FROM competencies c
                    LEFT JOIN domains d ON d.id = c.domain_id
                    ORDER BY c.code, c.name
                    """
                )
            )
        return db.rows_as_dicts(result)


@router.get("/api/milestones")
def milestones(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM milestones WHERE 1=1" + clause + " ORDER BY title"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


@router.get("/api/yccd")
def yccd(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM yccd WHERE 1=1" + clause + " ORDER BY code"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


@router.get("/api/activities")
def activities(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM activities WHERE 1=1" + clause + " ORDER BY code, title"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


@router.get("/api/rubrics")
def rubrics(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        if age_group:
            result = conn.execute(
                text(
                    """
                    SELECT r.*
                    FROM rubrics r
                    JOIN yccd y ON y.id = r.yccd_id
                    JOIN age_groups ag ON ag.id = y.age_group_id
                    WHERE ag.code = :age_code OR ag.name LIKE :age_like
                    ORDER BY r.title
                    """
                ),
                {"age_code": age_group, "age_like": f"%{age_group}%"},
            )
        else:
            result = conn.execute(text("SELECT * FROM rubrics ORDER BY title"))
        return db.rows_as_dicts(result)


@router.get("/api/year-plans")
def year_plans(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM year_plans WHERE 1=1" + clause + " ORDER BY school_year, title"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)
