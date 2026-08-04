from typing import Any

from fastapi import APIRouter, Depends, Query

from backend import db
from backend.auth import CurrentUser, get_current_user

router = APIRouter(prefix="/api/audit-log", tags=["audit"])


@router.get("")
def list_audit_log(
    limit: int = Query(default=10, ge=1, le=100), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(
            db.audit_log.select()
            .filter_by(school_id=current_user.school_id)
            .order_by(db.audit_log.c.created_at.desc(), db.audit_log.c.id.desc())
            .limit(limit)
        )
        rows = db.rows_as_dicts(result)
        user_ids = {r["user_id"] for r in rows if r["user_id"]}
        names: dict[int, str] = {}
        if user_ids:
            user_rows = conn.execute(db.users.select().where(db.users.c.id.in_(user_ids)))
            names = {r["id"]: (r["full_name"] or r["email"]) for r in db.rows_as_dicts(user_rows)}
        for r in rows:
            r["user_name"] = names.get(r["user_id"], "")
        return rows
