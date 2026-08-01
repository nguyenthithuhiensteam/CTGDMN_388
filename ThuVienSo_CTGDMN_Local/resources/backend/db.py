from pathlib import Path
import sqlite3
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "database" / "ct388_local.db"


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fetch_table_counts(table_names: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with get_connection() as conn:
        for table_name in table_names:
            row = conn.execute(f'SELECT COUNT(*) AS total FROM "{table_name}"').fetchone()
            counts[table_name] = int(row["total"] if row else 0)
    return counts
