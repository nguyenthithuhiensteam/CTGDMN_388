from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from backend import db
from backend.audit import write_audit_log
from backend.auth import CurrentUser, get_current_user, require_superadmin

router = APIRouter(prefix="/api/superadmin", tags=["superadmin"])

_VALID_STATUSES = {"pending", "approved", "rejected"}


@router.get("/schools")
def list_schools(
    status: str = Query(default="pending"), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    require_superadmin(current_user)
    with db.get_connection() as conn:
        query = db.schools.select().order_by(db.schools.c.created_at.desc())
        if status != "all":
            if status not in _VALID_STATUSES:
                raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ.")
            query = query.filter_by(status=status)
        rows = db.rows_as_dicts(conn.execute(query))
        school_ids = [r["id"] for r in rows]
        user_counts: dict[int, int] = {}
        admin_emails: dict[int, str] = {}
        if school_ids:
            count_rows = conn.execute(
                select(db.users.c.school_id, func.count(db.users.c.id))
                .where(db.users.c.school_id.in_(school_ids))
                .group_by(db.users.c.school_id)
            )
            user_counts = dict(count_rows.all())
            admin_rows = conn.execute(
                db.users.select().where(db.users.c.school_id.in_(school_ids)).where(db.users.c.role == "admin")
            )
            for r in db.rows_as_dicts(admin_rows):
                admin_emails.setdefault(r["school_id"], r["email"])
        for r in rows:
            r["user_count"] = user_counts.get(r["id"], 0)
            r["admin_email"] = admin_emails.get(r["id"], "")
        return rows


@router.post("/schools/{school_id}/approve")
def approve_school(school_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    require_superadmin(current_user)
    with db.get_connection() as conn:
        with conn.begin():
            school = conn.execute(db.schools.select().filter_by(id=school_id)).mappings().fetchone()
            if not school:
                raise HTTPException(status_code=404, detail="Không tìm thấy trường.")
            conn.execute(db.schools.update().where(db.schools.c.id == school_id).values(status="approved"))
            write_audit_log(conn, school_id, None, "approve", "school", school_id, school["name"])
    return {"status": "ok"}


@router.post("/schools/{school_id}/reject")
def reject_school(school_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    require_superadmin(current_user)
    with db.get_connection() as conn:
        with conn.begin():
            school = conn.execute(db.schools.select().filter_by(id=school_id)).mappings().fetchone()
            if not school:
                raise HTTPException(status_code=404, detail="Không tìm thấy trường.")
            conn.execute(db.schools.update().where(db.schools.c.id == school_id).values(status="rejected"))
            write_audit_log(conn, school_id, None, "reject", "school", school_id, school["name"])
    return {"status": "ok"}


@router.post("/reimport-core-data")
def reimport_core_data(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    """Chạy lại import dữ liệu lõi CT388 (YCCĐ/mốc phát triển/hoạt động/rubric...)
    từ 2 file Excel gốc. An toàn để gọi bất cứ lúc nào: chỉ upsert theo mã ổn định
    (không xóa dữ liệu lõi cũ), không đụng tới dữ liệu riêng của từng trường
    (trẻ, kế hoạch, tài khoản...). Dùng để áp bản sửa lỗi import (domains rác,
    thiếu mốc phát triển nhà trẻ) vào một database đã import từ trước."""
    require_superadmin(current_user)
    before = db.fetch_table_counts(
        ["domains", "yccd", "milestones", "activities", "rubrics", "competencies", "year_plans"]
    )
    from backend.backup import backup_database
    from backend.import_core_excel import MG, NT, run_import

    if not (MG.exists() and NT.exists()):
        raise HTTPException(status_code=400, detail="Không tìm thấy file Excel nguồn trên server.")
    backup_database()
    results = run_import()
    after = db.fetch_table_counts(
        ["domains", "yccd", "milestones", "activities", "rubrics", "competencies", "year_plans"]
    )
    return {
        "status": "ok",
        "before": before,
        "after": after,
        "sheets": [
            {"sheet": r["sheet"], "read": r["rows"], "imported": r["ok"], "skipped": r["skip"]} for r in results
        ],
    }
