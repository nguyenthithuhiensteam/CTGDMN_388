from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend import db
from backend.audit import write_audit_log
from backend.auth import CurrentUser, get_current_user, require_admin

router = APIRouter(tags=["children"])


def _tenant_table_crud_get(table, current_user: CurrentUser, **filters) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        stmt = table.select().filter_by(school_id=current_user.school_id, **filters)
        result = conn.execute(stmt)
        return db.rows_as_dicts(result)


class ChildRequest(BaseModel):
    full_name: str
    child_code: str = ""
    date_of_birth: str = ""
    gender: str = ""
    class_name: str = ""
    age_group_id: int | None = None
    notes: str = ""


@router.get("/api/children")
def list_children(current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _tenant_table_crud_get(db.children, current_user)


@router.post("/api/children")
def create_child(payload: ChildRequest, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            child_id = db.insert_returning_id(
                conn,
                db.children,
                {"school_id": current_user.school_id, **payload.model_dump()},
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "child", child_id, payload.full_name
            )
    return {"status": "ok", "id": child_id}


@router.delete("/api/children/{child_id}")
def delete_child(child_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            conn.execute(db.children.delete().filter_by(id=child_id, school_id=current_user.school_id))
            write_audit_log(conn, current_user.school_id, current_user.user_id, "delete", "child", child_id, "")
    return {"status": "ok"}


class ObservationRequest(BaseModel):
    child_id: int
    observed_at: str = ""
    context: str = ""
    note: str
    evidence: str = ""
    support_next: str = ""


@router.get("/api/observations")
def list_observations(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.observations, current_user, **filters)


@router.post("/api/observations")
def create_observation(
    payload: ObservationRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            obs_id = db.insert_returning_id(
                conn,
                db.observations,
                {"school_id": current_user.school_id, **payload.model_dump()},
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "observation", obs_id, payload.note[:200]
            )
    return {"status": "ok", "id": obs_id}


class AssessmentRequest(BaseModel):
    child_id: int
    yccd_id: int | None = None
    assessment_date: str = ""
    evidence: str = ""
    progress_note: str = ""
    support_next: str = ""


@router.get("/api/assessments")
def list_assessments(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.assessments, current_user, **filters)


@router.post("/api/assessments")
def create_assessment(
    payload: AssessmentRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            a_id = db.insert_returning_id(
                conn,
                db.assessments,
                {"school_id": current_user.school_id, **payload.model_dump()},
            )
            write_audit_log(conn, current_user.school_id, current_user.user_id, "create", "assessment", a_id, "")
    return {"status": "ok", "id": a_id}


class PortfolioRequest(BaseModel):
    child_id: int
    title: str
    artifact_type: str = ""
    artifact_path: str = ""
    note: str = ""


@router.get("/api/portfolio")
def list_portfolio(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.portfolio, current_user, **filters)


@router.post("/api/portfolio")
def create_portfolio_item(
    payload: PortfolioRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            p_id = db.insert_returning_id(
                conn,
                db.portfolio,
                {"school_id": current_user.school_id, **payload.model_dump()},
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "portfolio", p_id, payload.title
            )
    return {"status": "ok", "id": p_id}


class SchoolSettingsRequest(BaseModel):
    school_name: str = ""
    school_year: str = ""
    city: str = ""
    principal_name: str = ""
    contact_info: str = ""


@router.get("/api/school-settings")
def get_school_settings(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        row = conn.execute(
            db.school_settings.select().filter_by(school_id=current_user.school_id)
        ).mappings().fetchone()
        return dict(row) if row else {}


@router.put("/api/school-settings")
def put_school_settings(
    payload: SchoolSettingsRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    require_admin(current_user)
    with db.get_connection() as conn:
        with conn.begin():
            settings_id = db.upsert_returning_id(
                conn,
                db.school_settings,
                {"school_id": current_user.school_id, **payload.model_dump()},
                conflict_cols=["school_id"],
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "update", "school_settings", settings_id, ""
            )
    return {"status": "ok", "id": settings_id}
