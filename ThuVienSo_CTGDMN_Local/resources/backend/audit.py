from __future__ import annotations

from typing import Any

from sqlalchemy.engine import Connection

from backend import db


def write_audit_log(
    conn: Connection,
    school_id: int | None,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    detail: str = "",
) -> None:
    """Best-effort audit trail entry. Never raises — a failed audit write should
    never block the actual operation it's describing."""
    try:
        db.insert_returning_id(
            conn,
            db.audit_log,
            {
                "school_id": school_id,
                "user_id": user_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "detail": detail,
            },
        )
    except Exception as exc:  # pragma: no cover - audit is best-effort
        print(f"[audit] Không ghi được audit log ({action} {entity_type}): {exc}")
