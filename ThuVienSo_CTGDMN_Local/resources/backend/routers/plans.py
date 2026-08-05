"""Chuỗi lập kế hoạch liên thông: mục tiêu năm -> 35 tuần -> ... -> giáo án.

Theo skill lập kế hoạch (phương pháp luận CT388): mục tiêu năm phân giải từ
YCCĐ nguồn (outcome_id = yccd_id, mã ổn định không đổi giữa các cấp kế
hoạch), 35 tuần phân bổ mục tiêu trọng tâm theo vòng xoắn làm quen -> hình
thành -> củng cố -> vận dụng. Tháng/Tuần/Ngày sẽ nối tiếp ở lượt sau; giáo án
ngày đã có sẵn qua Trợ lý AI.
"""

import json
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import db
from backend.audit import write_audit_log
from backend.auth import CurrentUser, get_current_user, require_admin

router = APIRouter(prefix="/api/plans", tags=["plans"])


def _assert_owns_annual_plan(conn, annual_plan_id: int, school_id: int) -> None:
    row = conn.execute(
        db.school_annual_plans.select().filter_by(id=annual_plan_id, school_id=school_id)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy kế hoạch năm của trường bạn.")


# ─── MỤC TIÊU NĂM (school_annual_plans) ─────────────────────────────────────
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


@router.post("/annual/{plan_id}/approve")
def approve_annual_plan(plan_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    require_admin(current_user)
    with db.get_connection() as conn:
        with conn.begin():
            _assert_owns_annual_plan(conn, plan_id, current_user.school_id)
            conn.execute(
                db.school_annual_plans.update()
                .where(db.school_annual_plans.c.id == plan_id)
                .values(status="approved", approved_by=current_user.user_id)
            )
            write_audit_log(conn, current_user.school_id, current_user.user_id, "approve", "annual_plan", plan_id)
    return {"status": "ok"}


# ─── MỤC TIÊU NĂM CHI TIẾT (annual_plan_goals, phân giải theo YCCĐ) ─────────
class AnnualGoalRequest(BaseModel):
    yccd_id: int | None = None
    goal_text: str
    content_text: str = ""
    context_text: str = ""
    stage: str = ""
    evidence_text: str = ""
    differentiation_text: str = ""


@router.get("/annual/{plan_id}/goals")
def list_annual_goals(plan_id: int, current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        _assert_owns_annual_plan(conn, plan_id, current_user.school_id)
        rows = db.rows_as_dicts(
            conn.execute(
                db.annual_plan_goals.select()
                .filter_by(school_annual_plan_id=plan_id)
                .order_by(db.annual_plan_goals.c.sort_order, db.annual_plan_goals.c.id)
            )
        )
        yccd_ids = [r["yccd_id"] for r in rows if r["yccd_id"]]
        yccd_map: dict[int, dict[str, Any]] = {}
        if yccd_ids:
            yccd_rows = conn.execute(db.yccd.select().where(db.yccd.c.id.in_(yccd_ids)))
            yccd_map = {r["id"]: {"code": r["code"], "content": r["content"]} for r in db.rows_as_dicts(yccd_rows)}
        for r in rows:
            r["yccd_code"] = yccd_map.get(r["yccd_id"], {}).get("code", "")
            r["yccd_content"] = yccd_map.get(r["yccd_id"], {}).get("content", "")
        return rows


@router.post("/annual/{plan_id}/goals")
def create_annual_goal(
    plan_id: int, payload: AnnualGoalRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            _assert_owns_annual_plan(conn, plan_id, current_user.school_id)
            goal_id = db.insert_returning_id(
                conn,
                db.annual_plan_goals,
                {"school_annual_plan_id": plan_id, **payload.model_dump()},
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "annual_plan_goal", goal_id,
                payload.goal_text[:200],
            )
    return {"status": "ok", "id": goal_id}


@router.put("/annual/goals/{goal_id}")
def update_annual_goal(
    goal_id: int, payload: AnnualGoalRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            goal_row = conn.execute(db.annual_plan_goals.select().filter_by(id=goal_id)).mappings().fetchone()
            if goal_row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy mục tiêu.")
            _assert_owns_annual_plan(conn, goal_row["school_annual_plan_id"], current_user.school_id)
            conn.execute(
                db.annual_plan_goals.update().where(db.annual_plan_goals.c.id == goal_id).values(**payload.model_dump())
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "update", "annual_plan_goal", goal_id,
                payload.goal_text[:200],
            )
    return {"status": "ok"}


@router.delete("/annual/goals/{goal_id}")
def delete_annual_goal(goal_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            goal_row = conn.execute(db.annual_plan_goals.select().filter_by(id=goal_id)).mappings().fetchone()
            if goal_row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy mục tiêu.")
            _assert_owns_annual_plan(conn, goal_row["school_annual_plan_id"], current_user.school_id)
            conn.execute(db.annual_plan_goals.delete().where(db.annual_plan_goals.c.id == goal_id))
            write_audit_log(conn, current_user.school_id, current_user.user_id, "delete", "annual_plan_goal", goal_id)
    return {"status": "ok"}


# ─── PHIÊN CHẾ 35 TUẦN (plan_35_weeks) ───────────────────────────────────────
class Week35Request(BaseModel):
    school_annual_plan_id: int
    week_number: int
    theme_title: str = ""
    date_range: str = ""


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
        rows = db.rows_as_dicts(result)
        for r in rows:
            try:
                r["goal_ids"] = json.loads(r["goal_ids"]) if r.get("goal_ids") else []
            except (TypeError, ValueError):
                r["goal_ids"] = []
        return rows


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


class Generate35WeeksRequest(BaseModel):
    school_annual_plan_id: int
    start_date: str  # YYYY-MM-DD, phải là thứ Hai
    skip_dates: list[str] = []  # danh sách thứ Hai của các tuần nghỉ, YYYY-MM-DD
    weeks: int = 35


@router.post("/35-weeks/generate")
def generate_35_weeks(
    payload: Generate35WeeksRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    """Tự tạo khung tuần từ ngày thứ Hai bắt đầu, bỏ qua các tuần nghỉ — theo
    đúng logic script tao_khung_35_tuan.py trong skill lập kế hoạch. Idempotent
    theo nghĩa an toàn gọi lại: xoá khung cũ (nếu có) của đúng plan này trước
    khi tạo lại, không đụng tới annual_plan_goals hay dữ liệu trường khác."""
    try:
        start = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu không hợp lệ (định dạng YYYY-MM-DD).")
    if start.weekday() != 0:
        raise HTTPException(status_code=400, detail="Ngày bắt đầu phải là thứ Hai.")
    skip: set[date] = set()
    for d in payload.skip_dates:
        try:
            skip.add(datetime.strptime(d, "%Y-%m-%d").date())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Ngày nghỉ không hợp lệ: {d}")

    with db.get_connection() as conn:
        with conn.begin():
            _assert_owns_annual_plan(conn, payload.school_annual_plan_id, current_user.school_id)
            conn.execute(
                db.plan_35_weeks.delete().where(
                    db.plan_35_weeks.c.school_annual_plan_id == payload.school_annual_plan_id
                )
            )
            current = start
            learning_week = 1
            created = 0
            max_iterations = (payload.weeks + len(skip) + 20) * 2  # chặn vòng lặp vô hạn nếu skip_dates bất thường
            iterations = 0
            while learning_week <= payload.weeks and iterations < max_iterations:
                iterations += 1
                end = current + timedelta(days=4)
                if current in skip:
                    db.insert_returning_id(
                        conn,
                        db.plan_35_weeks,
                        {
                            "school_annual_plan_id": payload.school_annual_plan_id,
                            "week_number": 0,
                            "theme_title": "Nghỉ",
                            "date_range": f"{current:%d/%m/%Y} - {end:%d/%m/%Y}",
                            "is_break": 1,
                        },
                    )
                else:
                    db.insert_returning_id(
                        conn,
                        db.plan_35_weeks,
                        {
                            "school_annual_plan_id": payload.school_annual_plan_id,
                            "week_number": learning_week,
                            "theme_title": "",
                            "date_range": f"{current:%d/%m/%Y} - {end:%d/%m/%Y}",
                            "is_break": 0,
                        },
                    )
                    learning_week += 1
                    created += 1
                current += timedelta(days=7)
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "create", "plan_35_week_batch",
                payload.school_annual_plan_id, f"Tạo khung {created} tuần từ {payload.start_date}",
            )
    return {"status": "ok", "weeks_created": created}


class UpdateWeekRequest(BaseModel):
    theme_title: str = ""
    goal_ids: list[int] = []


@router.put("/35-weeks/{week_id}")
def update_35_week(
    week_id: int, payload: UpdateWeekRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            week_row = conn.execute(db.plan_35_weeks.select().filter_by(id=week_id)).mappings().fetchone()
            if week_row is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy tuần.")
            _assert_owns_annual_plan(conn, week_row["school_annual_plan_id"], current_user.school_id)
            conn.execute(
                db.plan_35_weeks.update()
                .where(db.plan_35_weeks.c.id == week_id)
                .values(theme_title=payload.theme_title, goal_ids=json.dumps(payload.goal_ids))
            )
            write_audit_log(
                conn, current_user.school_id, current_user.user_id, "update", "plan_35_week", week_id,
                payload.theme_title[:200],
            )
    return {"status": "ok"}


@router.get("/annual/{plan_id}/coverage")
def goal_coverage(plan_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """Rà soát nhanh độ bao phủ: mục tiêu nào chưa được phân bổ vào tuần nào
    (mục tiêu 'mồ côi' theo đúng thuật ngữ trong skill lập kế hoạch)."""
    with db.get_connection() as conn:
        _assert_owns_annual_plan(conn, plan_id, current_user.school_id)
        goals = db.rows_as_dicts(
            conn.execute(db.annual_plan_goals.select().filter_by(school_annual_plan_id=plan_id))
        )
        weeks = db.rows_as_dicts(
            conn.execute(db.plan_35_weeks.select().filter_by(school_annual_plan_id=plan_id))
        )
        covered_goal_ids: set[int] = set()
        for w in weeks:
            try:
                covered_goal_ids.update(json.loads(w["goal_ids"]) if w.get("goal_ids") else [])
            except (TypeError, ValueError):
                pass
        orphan_goals = [g["id"] for g in goals if g["id"] not in covered_goal_ids]
        return {
            "total_goals": len(goals),
            "total_weeks": len([w for w in weeks if not w.get("is_break")]),
            "orphan_goal_ids": orphan_goals,
            "orphan_count": len(orphan_goals),
        }
