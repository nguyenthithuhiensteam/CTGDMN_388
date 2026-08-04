from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from backend.db import DATABASE_PATH, get_database_url, is_sqlite

BACKUP_DIR = DATABASE_PATH.parent / "backups"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def backup_database() -> Path | None:
    """Best-effort backup before a schema change. Never raises — a failed backup
    should not block app startup, but is logged loudly so it isn't silently missed."""
    try:
        if is_sqlite():
            if not DATABASE_PATH.exists():
                return None
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            dest = BACKUP_DIR / f"ct388_local_{_timestamp()}.db"
            shutil.copy2(DATABASE_PATH, dest)
            print(f"[backup] SQLite backup created: {dest}")
            return dest
        return _backup_postgres()
    except Exception as exc:  # pragma: no cover - best-effort only
        print(f"[backup] Bỏ qua backup (lỗi không chặn khởi động): {exc}")
        return None


def _backup_postgres() -> Path | None:
    if shutil.which("pg_dump") is None:
        print("[backup] Không tìm thấy pg_dump trên hệ thống — bỏ qua backup Postgres.")
        return None
    url = get_database_url()
    parsed = urlparse(url.replace("postgresql+psycopg://", "postgresql://", 1))
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"ct388_pg_{_timestamp()}.sql"
    env_url = f"postgresql://{parsed.netloc}{parsed.path}{('?' + parsed.query) if parsed.query else ''}"
    with open(dest, "w", encoding="utf-8") as f:
        result = subprocess.run(
            ["pg_dump", "--no-owner", "--no-privileges", env_url],
            stdout=f,
            stderr=subprocess.PIPE,
            timeout=120,
        )
    if result.returncode != 0:
        dest.unlink(missing_ok=True)
        print(f"[backup] pg_dump thất bại: {result.stderr.decode('utf-8', errors='replace')[:500]}")
        return None
    print(f"[backup] Postgres backup created: {dest}")
    return dest
