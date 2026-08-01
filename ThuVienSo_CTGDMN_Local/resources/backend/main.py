from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend import db
from backend.ai_config import clear_api_key, get_api_key, has_api_key, save_api_key
from backend.auth import CurrentUser, create_token, get_current_user, hash_password, require_admin, verify_password
from backend.init_db import TABLES, init_database
from backend.license_manager import create_license_for_current_machine, get_license_status, get_machine_id

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_AI_MODEL = "claude-sonnet-5"

app = FastAPI(
    title="CT388 App API",
    version="0.4.0",
    description="Backend for CT388 preschool education planning support (desktop + hosted web).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def age_filter(age_group: str | None) -> tuple[str, dict[str, Any]]:
    if not age_group:
        return "", {}
    return (
        " AND age_group_id IN (SELECT id FROM age_groups WHERE code=:age_code OR name LIKE :age_like)",
        {"age_code": age_group, "age_like": f"%{age_group}%"},
    )


@app.on_event("startup")
def on_startup() -> None:
    init_database()
    _seed_core_data_if_empty()


def _seed_core_data_if_empty() -> None:
    """First boot against a fresh database (e.g. a new hosted Postgres): load the
    shared CT388 curriculum data from the bundled Excel files, if present. Safe to
    skip on later restarts since it only runs while `domains` is still empty."""
    try:
        if db.fetch_table_counts(["domains"]).get("domains", 0) > 0:
            return
        from backend.import_core_excel import MG, NT, run_import

        if MG.exists() and NT.exists():
            run_import()
    except Exception as exc:  # pragma: no cover - best-effort seeding, never blocks startup
        print(f"[startup] Bỏ qua seed dữ liệu lõi: {exc}")


@app.get("/api/health")
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


@app.get("/api/stats")
def stats() -> dict[str, object]:
    counts = db.fetch_table_counts(TABLES)
    return {"status": "ok", "tables": counts, "total_records": sum(counts.values())}


@app.get("/api/age-groups")
def age_groups() -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(text("SELECT * FROM age_groups ORDER BY sort_order, code, name"))
        return db.rows_as_dicts(result)


@app.get("/api/domains")
def domains() -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        result = conn.execute(text("SELECT * FROM domains ORDER BY sort_order, code, name"))
        return db.rows_as_dicts(result)


@app.get("/api/competencies")
def competencies(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        if age_group:
            result = conn.execute(
                text(
                    """
                    SELECT DISTINCT c.*
                    FROM competencies c
                    JOIN yccd y ON y.competency_id = c.id
                    JOIN age_groups ag ON ag.id = y.age_group_id
                    WHERE ag.code = :age_code OR ag.name LIKE :age_like
                    ORDER BY c.code, c.name
                    """
                ),
                {"age_code": age_group, "age_like": f"%{age_group}%"},
            )
        else:
            result = conn.execute(text("SELECT * FROM competencies ORDER BY code, name"))
        return db.rows_as_dicts(result)


@app.get("/api/yccd")
def yccd(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM yccd WHERE 1=1" + clause + " ORDER BY code"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


@app.get("/api/activities")
def activities(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM activities WHERE 1=1" + clause + " ORDER BY code, title"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


@app.get("/api/rubrics")
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


@app.get("/api/year-plans")
def year_plans(age_group: str | None = Query(default=None)) -> list[dict[str, Any]]:
    clause, params = age_filter(age_group)
    sql = "SELECT * FROM year_plans WHERE 1=1" + clause + " ORDER BY school_year, title"
    with db.get_connection() as conn:
        result = conn.execute(text(sql), params)
        return db.rows_as_dicts(result)


# ─── Legacy desktop machine-lock license (single-install offline mode) ─────
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


# ─── Auth: school accounts (multi-tenant, hosted web mode) ─────────────────
class RegisterSchoolRequest(BaseModel):
    school_name: str
    city: str = ""
    admin_email: str
    admin_password: str
    admin_full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateTeacherRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class AuthResponse(BaseModel):
    token: str
    role: str
    school_id: int
    school_name: str
    full_name: str


def _login_response(conn, user_row) -> AuthResponse:
    school = conn.execute(db.schools.select().filter_by(id=user_row["school_id"])).mappings().fetchone()
    token = create_token(user_row["id"], user_row["school_id"], user_row["role"])
    return AuthResponse(
        token=token,
        role=user_row["role"],
        school_id=user_row["school_id"],
        school_name=school["name"] if school else "",
        full_name=user_row["full_name"] or "",
    )


@app.post("/api/auth/register-school", response_model=AuthResponse)
def register_school(payload: RegisterSchoolRequest) -> AuthResponse:
    if not payload.school_name.strip():
        raise HTTPException(status_code=400, detail="Vui lòng nhập tên trường.")
    if not payload.admin_email.strip() or len(payload.admin_password) < 6:
        raise HTTPException(status_code=400, detail="Email hợp lệ và mật khẩu tối thiểu 6 ký tự.")
    with db.get_connection() as conn:
        with conn.begin():
            try:
                school_id = db.insert_returning_id(
                    conn, db.schools, {"name": payload.school_name.strip(), "city": payload.city.strip()}
                )
                user_id = db.insert_returning_id(
                    conn,
                    db.users,
                    {
                        "school_id": school_id,
                        "email": payload.admin_email.strip().lower(),
                        "password_hash": hash_password(payload.admin_password),
                        "full_name": payload.admin_full_name.strip(),
                        "role": "admin",
                    },
                )
            except IntegrityError:
                raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
            user_row = conn.execute(db.users.select().filter_by(id=user_id)).mappings().fetchone()
            return _login_response(conn, user_row)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    with db.get_connection() as conn:
        user_row = conn.execute(
            db.users.select().filter_by(email=payload.email.strip().lower())
        ).mappings().fetchone()
        if not user_row or not verify_password(payload.password, user_row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
        return _login_response(conn, user_row)


@app.get("/api/auth/me")
def auth_me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        user_row = conn.execute(db.users.select().filter_by(id=current_user.user_id)).mappings().fetchone()
        school = conn.execute(db.schools.select().filter_by(id=current_user.school_id)).mappings().fetchone()
        return {
            "user_id": current_user.user_id,
            "email": user_row["email"] if user_row else "",
            "full_name": user_row["full_name"] if user_row else "",
            "role": current_user.role,
            "school_id": current_user.school_id,
            "school_name": school["name"] if school else "",
        }


@app.post("/api/auth/teachers")
def create_teacher(
    payload: CreateTeacherRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
    require_admin(current_user)
    if not payload.email.strip() or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Email hợp lệ và mật khẩu tối thiểu 6 ký tự.")
    with db.get_connection() as conn:
        with conn.begin():
            try:
                user_id = db.insert_returning_id(
                    conn,
                    db.users,
                    {
                        "school_id": current_user.school_id,
                        "email": payload.email.strip().lower(),
                        "password_hash": hash_password(payload.password),
                        "full_name": payload.full_name.strip(),
                        "role": "teacher",
                    },
                )
            except IntegrityError:
                raise HTTPException(status_code=409, detail="Email này đã được đăng ký.")
    return {"status": "ok", "user_id": user_id}


@app.get("/api/auth/teachers")
def list_teachers(current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    require_admin(current_user)
    with db.get_connection() as conn:
        result = conn.execute(
            db.users.select()
            .filter_by(school_id=current_user.school_id)
            .order_by(db.users.c.created_at)
        )
        return [
            {k: v for k, v in row.items() if k != "password_hash"}
            for row in db.rows_as_dicts(result)
        ]


# ─── Per-school data: children, observations, assessments, portfolio ───────
class ChildRequest(BaseModel):
    full_name: str
    child_code: str = ""
    date_of_birth: str = ""
    gender: str = ""
    class_name: str = ""
    age_group_id: int | None = None
    notes: str = ""


def _tenant_table_crud_get(table, current_user: CurrentUser, **filters) -> list[dict[str, Any]]:
    with db.get_connection() as conn:
        stmt = table.select().filter_by(school_id=current_user.school_id, **filters)
        result = conn.execute(stmt)
        return db.rows_as_dicts(result)


@app.get("/api/children")
def list_children(current_user: CurrentUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    return _tenant_table_crud_get(db.children, current_user)


@app.post("/api/children")
def create_child(payload: ChildRequest, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            child_id = db.insert_returning_id(
                conn,
                db.children,
                {"school_id": current_user.school_id, **payload.model_dump()},
            )
    return {"status": "ok", "id": child_id}


@app.delete("/api/children/{child_id}")
def delete_child(child_id: int, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        with conn.begin():
            conn.execute(db.children.delete().filter_by(id=child_id, school_id=current_user.school_id))
    return {"status": "ok"}


class ObservationRequest(BaseModel):
    child_id: int
    observed_at: str = ""
    context: str = ""
    note: str
    evidence: str = ""
    support_next: str = ""


@app.get("/api/observations")
def list_observations(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.observations, current_user, **filters)


@app.post("/api/observations")
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
    return {"status": "ok", "id": obs_id}


class AssessmentRequest(BaseModel):
    child_id: int
    yccd_id: int | None = None
    assessment_date: str = ""
    evidence: str = ""
    progress_note: str = ""
    support_next: str = ""


@app.get("/api/assessments")
def list_assessments(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.assessments, current_user, **filters)


@app.post("/api/assessments")
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
    return {"status": "ok", "id": a_id}


class PortfolioRequest(BaseModel):
    child_id: int
    title: str
    artifact_type: str = ""
    artifact_path: str = ""
    note: str = ""


@app.get("/api/portfolio")
def list_portfolio(
    child_id: int | None = Query(default=None), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict[str, Any]]:
    filters = {"child_id": child_id} if child_id is not None else {}
    return _tenant_table_crud_get(db.portfolio, current_user, **filters)


@app.post("/api/portfolio")
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
    return {"status": "ok", "id": p_id}


class SchoolSettingsRequest(BaseModel):
    school_name: str = ""
    school_year: str = ""
    city: str = ""
    principal_name: str = ""
    contact_info: str = ""


@app.get("/api/school-settings")
def get_school_settings(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    with db.get_connection() as conn:
        row = conn.execute(
            db.school_settings.select().filter_by(school_id=current_user.school_id)
        ).mappings().fetchone()
        return dict(row) if row else {}


@app.put("/api/school-settings")
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
    return {"status": "ok", "id": settings_id}


# ─── AI lesson-plan assistant (proxied server-side; requires login) ───────
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
def ai_config_set(payload: AiKeyRequest, current_user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    require_admin(current_user)
    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="API key không được để trống.")
    save_api_key(payload.api_key)
    return {"configured": True}


@app.delete("/api/ai/config")
def ai_config_delete(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, bool]:
    require_admin(current_user)
    clear_api_key()
    return {"configured": False}


@app.post("/api/ai/messages")
async def ai_messages(
    payload: AiMessageRequest, current_user: CurrentUser = Depends(get_current_user)
) -> dict[str, Any]:
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


# ─── Serve the static frontend (hosted web deployment) ─────────────────────
# Must stay last: routes registered above are matched first, so this catch-all
# mount only serves paths that aren't one of the /api/* routes.
_FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
