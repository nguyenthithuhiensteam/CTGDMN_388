"""Chuỗi lập kế hoạch liên thông: mục tiêu năm -> 35 tuần -> ... -> giáo án.

Giai đoạn 1: chỉ tạo endpoint CRUD cơ bản cho annual plan + 35 tuần để có chỗ
lưu dữ liệu thật; chưa có màn hình giao diện thao tác (sẽ làm ở Giai đoạn 3).
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import db
from backend.audit import write_audit_log
from backend.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/plans", tags=["plans"])


class AnnualPlanRequest(BaseModel):
    school_year: str
    age_group_id: int | None = None
    title: str = ""
    goals_summary: str = ""


@router.get("/annual")
def list_annual_plans(current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(db.school_annual_plans.select().filter_by(school_id=current_user.school_id))
        return db.rows_as_dicts(result)


@router.post("/annual")
def create_annual_plan(
    payload: AnnualPlanRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            plan_id = db.insert_returning_id(
                conn,
                db.school_annual_plans,
                {
                    "school_id": current_user.school_id,
                    "created_by": current_user.user_id,
                    **payload.model_dump(),
                },
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "annual_plan", plan_id, payload.title
            )
    return {"status": "ok", "id": plan_id}


class Week35Request(BaseModel):
    school_annual_plan_id: int
    week_number: int
    theme_title: str = ""
    date_range: str = ""


def _assert_owns_annual_plan(conn, annual_plan_id: int, school_id: int) -> None:
    row = conn.execute(
        db.school_annual_plans.select().filter_by(id=annual_plan_id, school_id=school_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy kế hoạch năm của trường bạn.")


@router.get("/35-weeks")
def list_35_weeks(
    school_annual_plan_id: int, current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        _assert_owns_annual_plan(conn, school_annual_plan_id, current_user.school_id)
        result = conn.execute(
            db.plan_35_weeks.select()
            .filter_by(school_annual_plan_id=school_annual_plan_id)
            .order_by(db.plan_35_weeks.c.week_number)
        )
        return db.rows_as_dicts(result)


@router.post("/35-weeks")
def create_35_week(payload: Week35Request, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            _assert_owns_annual_plan(conn, payload.school_annual_plan_id, current_user.school_id)
            week_id = db.insert_returning_id(conn, db.plan_35_weeks, payload.model_dump())
            write_audit_log(
                conn,
                current_user.school_id,
                current_user.user_id,
                "create",
                "plan_35_week",
                week_id,
                f"Tuần {payload.week_number}: {payload.theme_title}",
            )
    return {"status": "ok", "id": week_id}
