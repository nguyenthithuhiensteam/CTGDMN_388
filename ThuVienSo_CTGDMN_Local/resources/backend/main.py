from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.ai_config import clear_api_key, get_api_key, has_api_key, save_api_key
from backend.db import DATABASE_PATH, fetch_table_counts, get_connection
from backend.init_db import TABLES, init_database
from backend.license_manager import create_license_for_current_machine, get_license_status, get_machine_id

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_AI_MODEL = "claude-sonnet-5"

app = FastAPI(
    title="CT388 Local App API",
    version="0.3.0",
    description="Local backend for CT388 preschool education planning support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def rows(rows) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def age_filter(age_group: str | None) -> tuple[str, list[Any]]:
    if not age_group:
        return "", []
    return " AND age_group_id IN (SELECT id FROM age_groups WHERE code=? OR name LIKE ?)", [age_group, f"%{age_group}%"]


@app.on_event("startup")
def on_startup() -> None:
    init_database()


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app": "CT388 Local App",
        "database": str(DATABASE_PATH),
        "database_exists": DATABASE_PATH.exists(),
    }


@app.get("/api/stats")
def stats() -> dict[str, object]:
    counts = fetch_table_counts(TABLES)
    return {"status": "ok", "tables": counts, "total_records": sum(counts.values())}


@app.get("/api/age-groups")
def age_groups() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return rows(conn.execute("SELECT * FROM age_groups ORDER BY sort_order, code, name").fetchall())


@app.get("/api/domains")
def domains() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return rows(conn.execute("SELECT * FROM domains ORDER BY sort_order, code, name").fetchall())


@app.get("/api/competencies")
def competencies(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if age_group:
            data = conn.execute(
                """
                SELECT DISTINCT c.*
                FROM competencies c
                JOIN yccd y ON y.competency_id = c.id
                JOIN age_groups ag ON ag.id = y.age_group_id
                WHERE ag.code = ? OR ag.name LIKE ?
                ORDER BY c.code, c.name
                """,
                (age_group, f"%{age_group}%"),
            ).fetchall()
        else:
            data = conn.execute("SELECT * FROM competencies ORDER BY code, name").fetchall()
    return rows(data)


@app.get("/api/yccd")
def yccd(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = "SELECT * FROM yccd WHERE 1=1"
    params: list[Any] = []
    clause, values = age_filter(age_group)
    sql += clause + " ORDER BY code"
    params.extend(values)
    with get_connection() as conn:
        return rows(conn.execute(sql, params).fetchall())


@app.get("/api/activities")
def activities(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = "SELECT * FROM activities WHERE 1=1"
    params: list[Any] = []
    clause, values = age_filter(age_group)
    sql += clause + " ORDER BY code, title"
    params.extend(values)
    with get_connection() as conn:
        return rows(conn.execute(sql, params).fetchall())


@app.get("/api/rubrics")
def rubrics(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if age_group:
            data = conn.execute(
                """
                SELECT r.*
                FROM rubrics r
                JOIN yccd y ON y.id = r.yccd_id
                JOIN age_groups ag ON ag.id = y.age_group_id
                WHERE ag.code = ? OR ag.name LIKE ?
                ORDER BY r.title
                """,
                (age_group, f"%{age_group}%"),
            ).fetchall()
        else:
            data = conn.execute("SELECT * FROM rubrics ORDER BY title").fetchall()
    return rows(data)


@app.get("/api/year-plans")
def year_plans(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    sql = "SELECT * FROM year_plans WHERE 1=1"
    params: list[Any] = []
    clause, values = age_filter(age_group)
    sql += clause + " ORDER BY school_year, title"
    params.extend(values)
    with get_connection() as conn:
        return rows(conn.execute(sql, params).fetchall())

@app.get("/api/license/status")
def license_status() -> dict[str, Any]:
    return get_license_status()


@app.get("/api/license/machine-id")
def license_machine_id() -> dict[str, str]:
    return {"machine_id": get_machine_id()}


@app.post("/api/license/create-demo")
def license_create_demo() -> dict[str, Any]:
    data = create_license_for_current_machine()
    status = get_license_status()
    return {"status": "ok", "license": data, "license_status": status}


class AiKeyRequest(BaseModel):
    api_key: str


class AiMessageRequest(BaseModel):
    model: str = DEFAULT_AI_MODEL
    max_tokens: int = 3000
    system: str | None = None
    messages: list[dict[str, Any]]


@app.get("/api/ai/config-status")
def ai_config_status() -> dict[str, bool]:
    return {"configured": has_api_key()}


@app.post("/api/ai/config")
def ai_config_set(payload: AiKeyRequest) -> dict[str, bool]:
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key không được để trống.")
    save_api_key(payload.api_key)
    return {"configured": True}


@app.delete("/api/ai/config")
def ai_config_delete() -> dict[str, bool]:
    clear_api_key()
    return {"configured": False}


@app.post("/api/ai/messages")
async def ai_messages(payload: AiMessageRequest) -> dict[str, Any]:
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=412,
            detail="Chưa cấu hình Anthropic API key. Vào Cài đặt AI để thêm.",
        )
    body: dict[str, Any] = {
        "model": payload.model,
        "max_tokens": payload.max_tokens,
        "messages": payload.messages,
    }
    if payload.system:
        body["system"] = payload.system
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                json=body,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
            )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Không kết nối được tới Anthropic API: {exc}") from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()